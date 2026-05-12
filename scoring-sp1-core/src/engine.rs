//! SP1-compatible scoring engine (no_std, no chrono).
use alloc::collections::BTreeMap;
use alloc::string::{String, ToString};
use alloc::vec::Vec;
use scoring_types::{ScoreInput, ScoreOutput, SignalScore};
use crate::profiles;
use crate::date_parser;

/// Full scoring pipeline for SP1 guest.
pub fn score_user(input: &ScoreInput, role: Option<&str>) -> ScoreOutput {
    let profile = profiles::resolve_role_profile(role);
    let profile_name = profile.name.clone();
    let signal_results = extract_all_signals(input);
    let (overall_score, below, active_count) = calculate_overall_score(
        &signal_results, &profile.weights, &profile.confidence_thresholds,
    );
    let risk_flags = generate_risk_flags(&signal_results, &below, &profile_name);

    ScoreOutput {
        overall_score,
        signal_scores: signal_results,
        risk_flags,
        profile_name,
        signals_below_threshold: below,
        signals_scored: active_count,
    }
}

fn extract_all_signals(input: &ScoreInput) -> BTreeMap<String, SignalScore> {
    let mut r = BTreeMap::new();
    r.insert("commit_consistency".into(), commit_consistency(&input.commits));
    r.insert("language_diversity".into(), language_diversity(&input.repos));
    r.insert("issue_engagement".into(), issue_engagement(&input.issues));
    r.insert("pr_patterns".into(), pr_patterns(&input.prs));
    r.insert("project_ownership".into(), project_ownership(&input.repos, &input.prs));
    r.insert("review_patterns".into(), review_patterns(&input.prs));
    r.insert("response_time".into(), response_time(&input.prs, &input.issues));
    r.insert("readme_quality".into(), readme_quality(&input.repos, &input.readmes));
    r.insert("commit_semantics".into(), commit_semantics(&input.commits));
    r.insert("cicd_maturity".into(), cicd_maturity(&input.cicd_configs, &input.repos));
    r.insert("contribution_consistency".into(), contribution_consistency(&input.contributions, &input.commits));
    r.insert("ai_usage_patterns".into(), ai_usage_patterns(&input.commits));
    r
}

fn filter_by_confidence(sig: &BTreeMap<String, SignalScore>, w: &BTreeMap<String, f64>, th: &BTreeMap<String, f64>) -> (BTreeMap<String, SignalScore>, Vec<String>) {
    let mut active = BTreeMap::new();
    let mut below = Vec::new();
    for (n, r) in sig {
        if !w.contains_key(n) { continue; }
        let t = th.get(n).copied().unwrap_or(0.0);
        if t > 0.0 && r.confidence < t { below.push(n.clone()); }
        else { active.insert(n.clone(), r.clone()); }
    }
    (active, below)
}

fn calculate_overall_score(sig: &BTreeMap<String, SignalScore>, w: &BTreeMap<String, f64>, th: &BTreeMap<String, f64>) -> (f64, Vec<String>, usize) {
    let (active, below) = filter_by_confidence(sig, w, th);
    let n = active.len();
    if n == 0 { return (0.0, below, 0); }
    let ws: f64 = active.keys().filter_map(|k| w.get(k)).sum();
    if ws == 0.0 { return (0.0, below, n); }
    let ws2: f64 = active.iter().map(|(k, v)| v.score * w.get(k).copied().unwrap_or(0.0)).sum();
    (ws2 / ws, below, n)
}

fn generate_risk_flags(sig: &BTreeMap<String, SignalScore>, below: &[String], pn: &str) -> Vec<String> {
    let mut f = Vec::new();
    for (_, r) in sig {
        if r.score < 30.0 && r.confidence > 0.5 { f.push(alloc::format!("Low {} score", r.name.replace('_', " "))); }
        if r.confidence < 0.3 { f.push(alloc::format!("Low confidence in {}", r.name.replace('_', " "))); }
    }
    for s in below { f.push(alloc::format!("Insufficient confidence in {} for {} profile", s, pn)); }
    f
}

// ---- Signal implementations ----

fn v(pairs: &[(&str, serde_json::Value)]) -> BTreeMap<String, serde_json::Value> {
    pairs.iter().map(|(k, v)| (k.to_string(), v.clone())).collect()
}

fn j(v: impl serde::Serialize) -> serde_json::Value { serde_json::to_value(v).unwrap_or_default() }

fn commit_consistency(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() { return SignalScore::new("commit_consistency", 0.0, 0.0, v(&[("message", j("No commits found"))])); }
    let mut s: Vec<_> = commits.iter().collect();
    s.sort_by_key(|c| &c.date);
    let mut diffs: Vec<f64> = Vec::new();
    for i in 1..s.len() {
        if let Some(d) = date_parser::timestamp_diff_seconds(&s[i].date, &s[i-1].date) {
            if d > 0.0 { diffs.push(d); }
        }
    }
    if diffs.is_empty() { return SignalScore::new("commit_consistency", 50.0, 0.5, v(&[("message", j("Only one commit"))])); }
    let n = diffs.len() as f64;
    let avg: f64 = diffs.iter().sum::<f64>() / n;
    let var: f64 = diffs.iter().map(|d| (d - avg).powi(2)).sum::<f64>() / n;
    let std = var.sqrt();
    let score = if avg > 0.0 { (100.0 * (1.0 - std / avg)).clamp(0.0, 100.0) } else { 50.0 };
    SignalScore::new("commit_consistency", score, (0.9_f64).min(commits.len() as f64 / 100.0),
        v(&[("total_commits", j(commits.len())), ("avg_time_between_commits_hours", j(avg / 3600.0))]))
}

fn language_diversity(repos: &[scoring_types::RepoData]) -> SignalScore {
    if repos.is_empty() { return SignalScore::new("language_diversity", 0.0, 0.0, v(&[("message", j("No repos found"))])); }
    let mut lc: BTreeMap<String, i64> = BTreeMap::new();
    for r in repos { if let Some(ref l) = r.language { *lc.entry(l.clone()).or_insert(0) += 1; } }
    if lc.is_empty() { return SignalScore::new("language_diversity", 0.0, 0.0, v(&[("message", j("No languages"))])); }
    let t: f64 = lc.values().copied().sum::<i64>() as f64;
    let mut e = 0.0;
    for c in lc.values() { let p = *c as f64 / t; if p > 0.0 { e -= p * p.sqrt(); } }
    let me = (lc.len() as f64).sqrt();
    let score = if me > 0.0 { (e / me * 100.0).max(0.0).min(100.0) } else { 0.0 };
    SignalScore::new("language_diversity", score, (0.9_f64).min(repos.len() as f64 / 50.0),
        v(&[("unique_languages", j(lc.len()))]))
}

fn issue_engagement(issues: &[scoring_types::IssueData]) -> SignalScore {
    if issues.is_empty() { return SignalScore::new("issue_engagement", 0.0, 0.0, v(&[("message", j("No issues"))])); }
    let tc: i64 = issues.iter().map(|i| i.comments).sum();
    let closed = issues.iter().filter(|i| i.state == "CLOSED").count();
    let n = issues.len() as f64;
    let score = ((tc as f64 / n) * 20.0 + (closed as f64 / n) * 50.0).min(100.0);
    SignalScore::new("issue_engagement", score, (0.9_f64).min(issues.len() as f64 / 30.0),
        v(&[("total_issues", j(issues.len())), ("total_comments", j(tc))]))
}

fn pr_patterns(prs: &[scoring_types::PrData]) -> SignalScore {
    if prs.is_empty() { return SignalScore::new("pr_patterns", 0.0, 0.0, v(&[("message", j("No PRs"))])); }
    let n = prs.len() as f64;
    let merged = prs.iter().filter(|p| p.merged_at.is_some()).count();
    let mr = merged as f64 / n;
    let aa: f64 = prs.iter().map(|p| p.additions).sum::<i64>() as f64 / n;
    let ad: f64 = prs.iter().map(|p| p.deletions).sum::<i64>() as f64 / n;
    let af: f64 = prs.iter().map(|p| p.changed_files).sum::<i64>() as f64 / n;
    let bal = if aa + ad > 0.0 { aa.min(ad) / (aa + ad) } else { 0.0 };
    let score = (mr * 40.0 + bal * 30.0 + (1.0_f64).min(100.0 / (af + 1.0)) * 30.0).min(100.0);
    SignalScore::new("pr_patterns", score, (0.9_f64).min(prs.len() as f64 / 30.0),
        v(&[("total_prs", j(prs.len())), ("merged_prs", j(merged))]))
}

fn project_ownership(repos: &[scoring_types::RepoData], _prs: &[scoring_types::PrData]) -> SignalScore {
    if repos.is_empty() { return SignalScore::new("project_ownership", 0.0, 0.0, v(&[("message", j("No repos"))])); }
    let owned = repos.iter().filter(|r| !r.is_fork).count();
    let forked = repos.iter().filter(|r| r.is_fork).count();
    let t = repos.len();
    let or = owned as f64 / t as f64;
    let score = if owned > 0 && forked > 0 { 50.0 + (or - 0.5).abs() * 20.0 } else { or * 80.0 };
    SignalScore::new("project_ownership", score.min(100.0), (0.9_f64).min(t as f64 / 30.0),
        v(&[("total_repos", j(t)), ("owned_repos", j(owned)), ("forked_repos", j(forked))]))
}

fn review_patterns(prs: &[scoring_types::PrData]) -> SignalScore {
    if prs.is_empty() { return SignalScore::new("review_patterns", 0.0, 0.0, v(&[("message", j("No PRs"))])); }
    let tc: i64 = prs.iter().map(|p| p.comments + p.review_comments).sum();
    let avg = tc as f64 / prs.len() as f64;
    SignalScore::new("review_patterns", (avg * 20.0).min(100.0), (0.9_f64).min(prs.len() as f64 / 20.0),
        v(&[("total_review_comments", j(tc))]))
}

fn response_time(prs: &[scoring_types::PrData], issues: &[scoring_types::IssueData]) -> SignalScore {
    if prs.is_empty() && issues.is_empty() {
        return SignalScore::new("response_time", 0.0, 0.0, v(&[("message", j("No data"))]));
    }
    let mut times: Vec<f64> = Vec::new();
    for pr in prs {
        if let Some(ref m) = pr.merged_at {
            if let Some(d) = date_parser::timestamp_diff_seconds(m, &pr.created_at) {
                if d > 0.0 { times.push(d); }
            }
        }
    }
    for issue in issues {
        if let Some(ref c) = issue.closed_at {
            if let Some(d) = date_parser::timestamp_diff_seconds(c, &issue.created_at) {
                if d > 0.0 { times.push(d); }
            }
        }
    }
    if times.is_empty() { return SignalScore::new("response_time", 50.0, 0.5, v(&[("message", j("No completed items"))])); }
    let avg: f64 = times.iter().sum::<f64>() / times.len() as f64;
    let score = (100.0 - (avg.min(86400.0 * 7.0) / 86400.0) * 10.0).max(0.0);
    SignalScore::new("response_time", score, (0.9_f64).min(times.len() as f64 / 20.0),
        v(&[("avg_response_time_hours", j(avg / 3600.0)), ("total_completed", j(times.len()))]))
}

fn readme_quality(repos: &[scoring_types::RepoData], readmes: &BTreeMap<String, scoring_types::ReadmeData>) -> SignalScore {
    if repos.is_empty() { return SignalScore::new("readme_quality", 0.0, 0.0, v(&[("message", j("No repos"))])); }
    if readmes.is_empty() {
        let wd = repos.iter().filter(|r| r.description.is_some()).count();
        if wd == 0 { return SignalScore::new("readme_quality", 0.0, 0.5, v(&[("message", j("No descriptions"))])); }
        let tl: usize = repos.iter().filter_map(|r| r.description.as_ref()).map(|d| d.len()).sum();
        let al = tl as f64 / wd as f64;
        let score = ((wd as f64 / repos.len() as f64) * 50.0 + (al / 10.0).min(50.0)).min(100.0);
        return SignalScore::new("readme_quality", score, (0.7_f64).min(repos.len() as f64 / 30.0),
            v(&[("repos_with_description", j(wd)), ("mode", j("description_fallback"))]));
    }
    let mut rwr = 0i64; let mut tc = 0i64; let mut ts = 0i64; let mut tcb = 0i64; let mut tb = 0i64; let mut repos_with_emoji = 0i64; let mut total_lists = 0i64;
    for repo in repos {
        if let Some(rm) = readmes.get(&repo.full_name) {
            if rm.content.is_some() { rwr += 1; if let Some(ref c) = rm.content { tc += c.len() as i64; } ts += rm.detected_sections.len() as i64; tcb += rm.code_block_count; tb += rm.badge_count; total_lists += rm.list_count; if rm.has_emoji { repos_with_emoji += 1; } }
        }
    }
    if rwr == 0 { return SignalScore::new("readme_quality", 0.0, 0.5, v(&[("message", j("No READMEs"))])); }
    let score = ((rwr as f64 / repos.len() as f64) * 30.0
        + (ts as f64 / rwr as f64 * 5.0 + tcb as f64 / rwr as f64 * 3.0 + total_lists as f64 / rwr as f64 * 1.5).min(30.0)
        + (tc as f64 / rwr as f64 / 66.7).min(15.0) + (tb as f64 / rwr as f64 * 2.0).min(10.0)
        + (repos_with_emoji as f64 / rwr as f64) * 15.0).min(100.0);
    SignalScore::new("readme_quality", score, (0.9_f64).min(rwr as f64 / 20.0),
        v(&[("repos_with_readme", j(rwr)), ("avg_char_count", j((tc as f64 / rwr as f64 * 10.0).round() / 10.0)), ("avg_sections", j((ts as f64 / rwr as f64 * 10.0).round() / 10.0)), ("avg_code_blocks", j((tcb as f64 / rwr as f64 * 10.0).round() / 10.0)), ("avg_lists", j((total_lists as f64 / rwr as f64 * 10.0).round() / 10.0)), ("avg_badges", j((tb as f64 / rwr as f64 * 10.0).round() / 10.0)), ("emoji_ratio", j((repos_with_emoji as f64 / rwr as f64 * 100.0).round() / 100.0)), ("mode", j("readme_content"))]))
}

fn commit_semantics(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() { return SignalScore::new("commit_semantics", 0.0, 0.0, v(&[("message", j("No commits"))])); }
    let n = commits.len() as f64;
    let cc = ["feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert"];
    let iv = ["add","remove","fix","update","change","implement","refactor","rename","move","delete","create","merge","bump","upgrade","downgrade","revert","introduce","extract","replace","migrate","enable","disable","improve","simplify","clean","bootstrap","initialize","convert","handle","support"];
    let mut ccnt = 0u64; let mut ml = 0u64; let mut tl: usize = 0; let mut icnt = 0u64;
    for c in commits {
        tl += c.message.len();
        if let Some(pos) = c.message.find(':') {
            let prefix = &c.message[..pos];
            if cc.iter().any(|t| prefix == *t || prefix == &alloc::format!("{}!", t) || prefix.starts_with(&alloc::format!("{}(", t))) { ccnt += 1; }
        }
        if c.message.contains('\n') && c.message.lines().filter(|l| !l.trim().is_empty()).count() > 1 { ml += 1; }
        if let Some(subj) = c.message.lines().next() {
            let after = subj.find(':').map(|i| &subj[i+1..]).unwrap_or(subj);
            if let Some(fw) = after.trim().split_whitespace().next() {
                let fw = fw.trim_end_matches(|c: char| c == '.' || c == ',' || c == '!' || c == ';').to_lowercase();
                if iv.contains(&fw.as_str()) { icnt += 1; }
            }
        }
    }
    let cr = ccnt as f64 / n; let ar = tl as f64 / n; let mr = ml as f64 / n; let ir = icnt as f64 / n;
    let score = (cr * 30.0 + (ar / 50.0 * 25.0).min(25.0) + mr * 25.0 + ir * 20.0).min(100.0);
    SignalScore::new("commit_semantics", score, (0.9_f64).min(commits.len() as f64 / 100.0),
        v(&[("total_commits", j(commits.len())), ("conventional_commit_ratio", j((cr*100.0).round()/100.0)), ("avg_message_length", j((ar*10.0).round()/10.0)), ("multi_line_ratio", j((mr*100.0).round()/100.0)), ("imperative_mood_ratio", j((ir*100.0).round()/100.0))]))
}

fn cicd_maturity(cicd: &BTreeMap<String, Vec<scoring_types::CicdConfigData>>, repos: &[scoring_types::RepoData]) -> SignalScore {
    if cicd.is_empty() || repos.is_empty() { return SignalScore::new("cicd_maturity", 0.0, 0.0, v(&[("message", j("No data"))])); }
    let tr = repos.len();
    let mut rc = 0; let mut at: BTreeMap<String, i64> = BTreeMap::new();
    for (_, cfgs) in cicd {
        let has = cfgs.iter().any(|c| c.exists);
        if has { rc += 1; for c in cfgs { if c.exists { *at.entry(c.config_type.clone()).or_insert(0) += 1; } } }
    }
    if rc == 0 { return SignalScore::new("cicd_maturity", 0.0, 0.5, v(&[("message", j("No CI/CD"))])); }
    let p = (rc as f64 / tr as f64) * 30.0;
    let d = (at.len() as f64 * 7.5).min(30.0);
    let ga = at.get("github_actions").copied().unwrap_or(0);
    let dk = at.get("docker").copied().unwrap_or(0);
    let oth = at.keys().filter(|k| *k != "github_actions" && *k != "docker").count();
    let mut dp = 0.0; if ga > 0 { dp += 20.0; } if dk > 0 { dp += 10.0; } dp += oth as f64 * 15.0;
    let score = (p + d + dp.min(40.0)).min(100.0);
    SignalScore::new("cicd_maturity", score, (0.85_f64).min(0.3 + rc as f64 / tr as f64 * 0.5),
        v(&[("repos_with_ci", j(rc)), ("ci_type_count", j(at.len()))]))
}

fn contribution_consistency(contributions: &Option<scoring_types::ContributionData>, commits: &[scoring_types::CommitData]) -> SignalScore {
    if let Some(ref c) = contributions {
        let days = &c.contribution_days;
        if days.is_empty() { return SignalScore::new("contribution_consistency", 0.0, 0.5, v(&[("message", j("Empty calendar"))])); }
        let td = days.len() as f64;
        let ad = days.iter().filter(|d| d.contribution_count > 0).count() as f64;
        let ar = ad / td;
        let mg = days.iter().fold((0i64, 0i64), |(mx, cur), d| {
            if d.contribution_count == 0 { (mx.max(cur+1), cur+1) } else { (mx, 0) }
        }).0;
        let gs = if mg >= 30 { 0.0 } else if mg >= 14 { 10.0 } else if mg >= 7 { 20.0 } else { 35.0 };
        let score = (ar * 35.0 + gs + 30.0 * ar).min(100.0);
        return SignalScore::new("contribution_consistency", score, (0.9_f64).min(0.4 + ar * 0.5),
            v(&[("total_days", j(days.len())), ("activity_ratio", j((ar*1000.0).round()/1000.0))]));
    }
    if commits.is_empty() { return SignalScore::new("contribution_consistency", 0.0, 0.0, v(&[("message", j("No data"))])); }
    if commits.len() < 2 { return SignalScore::new("contribution_consistency", 25.0, 0.3, v(&[("message", j("Too few commits"))])); }
    let mut s: Vec<_> = commits.iter().collect(); s.sort_by_key(|c| &c.date);
    let first = s[0].date.clone(); let last = s[s.len()-1].date.clone();
    if let (Some(t1), Some(t2)) = (date_parser::parse_timestamp(&first), date_parser::parse_timestamp(&last)) {
        let span = (t2 - t1) as f64 / 86400.0; let cpd = commits.len() as f64 / span.max(1.0);
        let dens = if (0.5..=3.0).contains(&cpd) { 60.0 } else if cpd < 0.5 { 30.0 + (cpd/0.5)*30.0 } else { (60.0 - (cpd-3.0)*5.0).max(10.0) };
        let mg = (1..s.len()).filter_map(|i| {
            match (date_parser::parse_timestamp(&s[i-1].date), date_parser::parse_timestamp(&s[i].date)) {
                (Some(a), Some(b)) => Some((b - a) as f64 / 86400.0), _ => None
            }
        }).fold(0.0_f64, f64::max);
        let gap = if mg >= 30.0 { 20.0 } else if mg >= 14.0 { 35.0 } else { 50.0 };
        let score = ((dens + gap) / 2.0).min(100.0);
        SignalScore::new("contribution_consistency", score, (0.5_f64).min(0.2 + commits.len() as f64/200.0),
            v(&[("total_commits", j(commits.len())), ("mode", j("commit_fallback"))]))
    } else {
        SignalScore::new("contribution_consistency", 0.0, 0.0, v(&[("message", j("Parse error"))]))
    }
}

fn ai_usage_patterns(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() { return SignalScore::new("ai_usage_patterns", 50.0, 0.0, v(&[("message", j("No commits"))])); }
    let n = commits.len() as f64;
    let lens: Vec<f64> = commits.iter().map(|c| c.message.len() as f64).collect();
    let avg_len: f64 = lens.iter().sum::<f64>() / n;
    let var = lens.iter().map(|l| (l - avg_len).powi(2)).sum::<f64>() / n; let std = var.sqrt();
    let style = if std < 5.0 { 5.0 } else if std < 10.0 { 20.0 } else if std < 30.0 { 35.0 } else if std < 50.0 { 25.0 } else { 15.0 };

    // ---- Timing cluster analysis ----
    let mut sorted: Vec<_> = commits.iter().collect();
    sorted.sort_by_key(|c| &c.date);

    let timing_score: f64 = if sorted.len() >= 2 {
        let mut time_diffs: Vec<f64> = Vec::new();
        for i in 1..sorted.len() {
            if let (Some(t1), Some(t2)) = (date_parser::parse_timestamp(&sorted[i-1].date), date_parser::parse_timestamp(&sorted[i].date)) {
                time_diffs.push((t2 - t1) as f64);
            }
        }

        if time_diffs.is_empty() {
            20.0
        } else {
            let avg_diff: f64 = time_diffs.iter().sum::<f64>() / time_diffs.len() as f64;

            // Detect burst clusters
            let mut burst_clusters = 0i64;
            let mut current_cluster = 1;
            for diff in &time_diffs {
                if *diff < 60.0 { current_cluster += 1; }
                else {
                    if current_cluster > 3 { burst_clusters += current_cluster; }
                    current_cluster = 1;
                }
            }
            if current_cluster > 3 { burst_clusters += current_cluster; }

            let br = burst_clusters as f64 / n;
            if br > 0.5 { 5.0 }
            else if br > 0.3 { 20.0 }
            else if br < 0.1 && avg_diff > 3600.0 { 35.0 }
            else if br < 0.2 { 30.0 }
            else { 25.0 }
        }
    } else {
        20.0
    };

    // ---- Conventional commit consistency ----
    let cc = ["feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert"];
    let ccn = commits.iter().filter(|c| {
        c.message.find(':').map(|p| {
            let prefix = &c.message[..p];
            cc.iter().any(|t| prefix == *t || prefix == &alloc::format!("{}!", t) || prefix.starts_with(&alloc::format!("{}(", t)))
        }).unwrap_or(false)
    }).count();
    let ccr = ccn as f64 / n;
    let ccs = if ccr > 0.95 && commits.len() >= 5 { 10.0 } else if ccr > 0.80 { 20.0 } else if ccr > 0.40 { 30.0 } else if ccr > 0.10 { 25.0 } else { 20.0 };
    let score = (style + timing_score + ccs).min(100.0);
    SignalScore::new("ai_usage_patterns", score, (0.85_f64).min(0.2 + (commits.len() as f64/100.0)*0.5),
        v(&[("total_commits", j(commits.len())), ("msg_length_std", j((std*10.0).round()/10.0)), ("avg_msg_length", j((avg_len*10.0).round()/10.0)), ("conventional_commit_ratio", j((ccr*100.0).round()/100.0))]))
}
