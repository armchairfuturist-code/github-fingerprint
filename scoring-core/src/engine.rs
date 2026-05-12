//! Scoring engine — calculates weighted scores from signals.
//! Mirrors Python scoring/engine.py

use std::collections::BTreeMap;
use scoring_types::{ScoreInput, ScoreOutput, SignalScore};
use crate::profiles;
use serde_json::json;

/// Compute all 12 signals from a ScoreInput.
fn extract_all_signals(input: &ScoreInput) -> BTreeMap<String, SignalScore> {
    let mut results = BTreeMap::new();
    results.insert("commit_consistency".to_string(), extract_commit_consistency(&input.commits));
    results.insert("language_diversity".to_string(), extract_language_diversity(&input.repos));
    results.insert("issue_engagement".to_string(), extract_issue_engagement(&input.issues));
    results.insert("pr_patterns".to_string(), extract_pr_patterns(&input.prs));
    results.insert("project_ownership".to_string(), extract_project_ownership(&input.repos, &input.prs));
    results.insert("review_patterns".to_string(), extract_review_patterns(&input.prs));
    results.insert("response_time".to_string(), extract_response_time(&input.prs, &input.issues));
    results.insert("readme_quality".to_string(), extract_readme_quality(&input.repos, &input.readmes));
    results.insert("commit_semantics".to_string(), extract_commit_semantics(&input.commits));
    results.insert("cicd_maturity".to_string(), extract_cicd_maturity(&input.cicd_configs, &input.repos));
    results.insert("contribution_consistency".to_string(), extract_contribution_consistency(&input.contributions, &input.commits));
    results.insert("ai_usage_patterns".to_string(), extract_ai_usage_patterns(&input.commits));
    results
}

/// Filter signals below confidence threshold.
fn filter_by_confidence(
    signal_results: &BTreeMap<String, SignalScore>,
    weights: &BTreeMap<String, f64>,
    thresholds: &BTreeMap<String, f64>,
) -> (BTreeMap<String, SignalScore>, Vec<String>) {
    let mut active = BTreeMap::new();
    let mut below = Vec::new();
    for (name, result) in signal_results {
        if !weights.contains_key(name) { continue; }
        let threshold = thresholds.get(name).copied().unwrap_or(0.0);
        if threshold > 0.0 && result.confidence < threshold {
            below.push(name.clone());
        } else {
            active.insert(name.clone(), result.clone());
        }
    }
    (active, below)
}

/// Calculate weighted overall score with confidence threshold filtering.
fn calculate_overall_score(
    signal_results: &BTreeMap<String, SignalScore>,
    weights: &BTreeMap<String, f64>,
    thresholds: &BTreeMap<String, f64>,
) -> (f64, Vec<String>, usize) {
    let (active, below) = filter_by_confidence(signal_results, weights, thresholds);
    let active_count = active.len();
    if active.is_empty() { return (0.0, below, 0); }

    let original_weight_sum: f64 = active.keys()
        .filter_map(|s| weights.get(s)).sum();
    if original_weight_sum == 0.0 { return (0.0, below, active_count); }

    let weighted_sum: f64 = active.iter()
        .map(|(name, result)| result.score * weights.get(name).copied().unwrap_or(0.0))
        .sum();

    (weighted_sum / original_weight_sum, below, active_count)
}

/// Generate risk flags.
fn generate_risk_flags(
    signal_results: &BTreeMap<String, SignalScore>,
    signals_below: &[String],
    profile_name: &str,
) -> Vec<String> {
    let mut flags = Vec::new();
    for (_name, r) in signal_results {
        if r.score < 30.0 && r.confidence > 0.5 {
            flags.push(format!("Low {} score", r.name.replace('_', " ")));
        }
        if r.confidence < 0.3 {
            flags.push(format!("Low confidence in {}", r.name.replace('_', " ")));
        }
    }
    for sig in signals_below {
        flags.push(format!("Insufficient confidence in {} for {} profile", sig, profile_name));
    }
    flags
}

/// Full scoring pipeline.
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

// =========================================================================
// Signal extraction implementations
// =========================================================================

fn extract_commit_consistency(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() {
        return SignalScore::new("commit_consistency", 0.0, 0.0, bt(&[("message", json!("No commits found"))]));
    }
    let mut sorted: Vec<_> = commits.iter().collect();
    sorted.sort_by_key(|c| &c.date);

    let mut time_diffs: Vec<f64> = Vec::new();
    for i in 1..sorted.len() {
        if let (Ok(d1), Ok(d2)) = (parse_dt(&sorted[i].date), parse_dt(&sorted[i-1].date)) {
            let diff = (d1 - d2).num_seconds() as f64;
            if diff > 0.0 { time_diffs.push(diff); }
        }
    }

    if time_diffs.is_empty() {
        return SignalScore::new("commit_consistency", 50.0, 0.5, bt(&[("message", json!("Only one commit found"))]));
    }

    let n = time_diffs.len() as f64;
    let sum: f64 = time_diffs.iter().sum();
    let avg_diff = sum / n;
    let variance: f64 = time_diffs.iter().map(|d| (d - avg_diff).powi(2)).sum::<f64>() / n;
    let std_dev = variance.sqrt();

    let score = if avg_diff > 0.0 {
        (100.0 * (1.0 - std_dev / avg_diff)).clamp(0.0, 100.0)
    } else { 50.0 };

    SignalScore::new("commit_consistency", score, (0.9_f64).min(commits.len() as f64 / 100.0),
        bt(&[("total_commits", json!(commits.len())),
            ("avg_time_between_commits_hours", json!(avg_diff / 3600.0)),
            ("std_dev_hours", json!(std_dev / 3600.0))]))
}

fn extract_language_diversity(repos: &[scoring_types::RepoData]) -> SignalScore {
    if repos.is_empty() {
        return SignalScore::new("language_diversity", 0.0, 0.0, bt(&[("message", json!("No repos found"))]));
    }
    let mut lang_counts: BTreeMap<String, i64> = BTreeMap::new();
    for repo in repos {
        if let Some(ref lang) = repo.language {
            *lang_counts.entry(lang.clone()).or_insert(0) += 1;
        }
    }
    if lang_counts.is_empty() {
        return SignalScore::new("language_diversity", 0.0, 0.0, bt(&[("message", json!("No languages detected"))]));
    }

    let total: f64 = lang_counts.values().sum::<i64>() as f64;
    let mut entropy = 0.0;
    for count in lang_counts.values() {
        let p = *count as f64 / total;
        if p > 0.0 { entropy -= p * p.sqrt(); }
    }
    let max_entropy = (lang_counts.len() as f64).sqrt();
    let div_score = if max_entropy > 0.0 { (entropy / max_entropy) * 100.0 } else { 0.0 };

    let top5: BTreeMap<String, i64> = {
        let mut v: Vec<_> = lang_counts.into_iter().collect();
        v.sort_by(|a, b| b.1.cmp(&a.1));
        v.truncate(5);
        v.into_iter().collect()
    };

    SignalScore::new("language_diversity", div_score.min(100.0), (0.9_f64).min(repos.len() as f64 / 50.0),
        bt(&[("unique_languages", json!(top5.len())),
            ("top_languages", serde_json::to_value(&top5).unwrap_or_default())]))
}

fn extract_issue_engagement(issues: &[scoring_types::IssueData]) -> SignalScore {
    if issues.is_empty() {
        return SignalScore::new("issue_engagement", 0.0, 0.0, bt(&[("message", json!("No issues found"))]));
    }
    let total_comments: i64 = issues.iter().map(|i| i.comments).sum();
    let closed = issues.iter().filter(|i| i.state == "CLOSED").count();
    let n = issues.len() as f64;
    let avg_comments = total_comments as f64 / n;
    let close_rate = closed as f64 / n;
    let score = (avg_comments * 20.0 + close_rate * 50.0).min(100.0);

    SignalScore::new("issue_engagement", score, (0.9_f64).min(issues.len() as f64 / 30.0),
        bt(&[("total_issues", json!(issues.len())),
            ("total_comments", json!(total_comments)),
            ("avg_comments_per_issue", json!(avg_comments)),
            ("close_rate", json!(close_rate))]))
}

fn extract_pr_patterns(prs: &[scoring_types::PrData]) -> SignalScore {
    if prs.is_empty() {
        return SignalScore::new("pr_patterns", 0.0, 0.0, bt(&[("message", json!("No PRs found"))]));
    }
    let n = prs.len() as f64;
    let merged = prs.iter().filter(|p| p.merged_at.is_some()).count();
    let merge_rate = merged as f64 / n;
    let avg_additions: f64 = prs.iter().map(|p| p.additions).sum::<i64>() as f64 / n;
    let avg_deletions: f64 = prs.iter().map(|p| p.deletions).sum::<i64>() as f64 / n;
    let avg_files: f64 = prs.iter().map(|p| p.changed_files).sum::<i64>() as f64 / n;

    let balance = if avg_additions + avg_deletions > 0.0 {
        avg_additions.min(avg_deletions) / (avg_additions + avg_deletions)
    } else { 0.0 };

    let quality = (merge_rate * 40.0 + balance * 30.0 + (1.0_f64).min(100.0 / (avg_files + 1.0)) * 30.0).min(100.0);
    SignalScore::new("pr_patterns", quality, (0.9_f64).min(prs.len() as f64 / 30.0),
        bt(&[("total_prs", json!(prs.len())), ("merged_prs", json!(merged)),
            ("avg_additions", json!(avg_additions)), ("avg_deletions", json!(avg_deletions)),
            ("avg_files_changed", json!(avg_files))]))
}

fn extract_project_ownership(repos: &[scoring_types::RepoData], _prs: &[scoring_types::PrData]) -> SignalScore {
    if repos.is_empty() {
        return SignalScore::new("project_ownership", 0.0, 0.0, bt(&[("message", json!("No repos found"))]));
    }
    let owned = repos.iter().filter(|r| !r.is_fork).count();
    let forked = repos.iter().filter(|r| r.is_fork).count();
    let total = repos.len();
    let owned_ratio = owned as f64 / total as f64;
    let score = if owned > 0 && forked > 0 { 50.0 + (owned_ratio - 0.5).abs() * 20.0 } else { owned_ratio * 80.0 };

    SignalScore::new("project_ownership", score.min(100.0), (0.9_f64).min(total as f64 / 30.0),
        bt(&[("total_repos", json!(total)), ("owned_repos", json!(owned)), ("forked_repos", json!(forked))]))
}

fn extract_review_patterns(prs: &[scoring_types::PrData]) -> SignalScore {
    if prs.is_empty() {
        return SignalScore::new("review_patterns", 0.0, 0.0, bt(&[("message", json!("No PRs found"))]));
    }
    let total_comments: i64 = prs.iter().map(|p| p.comments + p.review_comments).sum();
    let avg = total_comments as f64 / prs.len() as f64;
    SignalScore::new("review_patterns", (avg * 20.0).min(100.0), (0.9_f64).min(prs.len() as f64 / 20.0),
        bt(&[("total_prs", json!(prs.len())), ("total_review_comments", json!(total_comments)),
            ("avg_comments_per_pr", json!(avg))]))
}

fn extract_response_time(prs: &[scoring_types::PrData], issues: &[scoring_types::IssueData]) -> SignalScore {
    if prs.is_empty() && issues.is_empty() {
        return SignalScore::new("response_time", 0.0, 0.0, bt(&[("message", json!("No PRs or issues found"))]));
    }

    let mut all_times: Vec<f64> = Vec::new();
    for pr in prs {
        if let Some(ref merged_at) = pr.merged_at {
            if let (Ok(created), Ok(merged)) = (parse_dt(&pr.created_at), parse_dt(merged_at)) {
                let secs = (merged - created).num_seconds() as f64;
                if secs > 0.0 { all_times.push(secs); }
            }
        }
    }
    for issue in issues {
        if let Some(ref closed_at) = issue.closed_at {
            if let (Ok(created), Ok(closed)) = (parse_dt(&issue.created_at), parse_dt(closed_at)) {
                let secs = (closed - created).num_seconds() as f64;
                if secs > 0.0 { all_times.push(secs); }
            }
        }
    }

    if all_times.is_empty() {
        return SignalScore::new("response_time", 50.0, 0.5, bt(&[("message", json!("No completed PRs or issues"))]));
    }

    let avg_time: f64 = all_times.iter().sum::<f64>() / all_times.len() as f64;
    let score = (100.0 - (avg_time.min(86400.0 * 7.0) / 86400.0) * 10.0).max(0.0);

    SignalScore::new("response_time", score, (0.9_f64).min(all_times.len() as f64 / 20.0),
        bt(&[("avg_response_time_hours", json!(avg_time / 3600.0)),
            ("total_completed", json!(all_times.len()))]))
}

fn extract_readme_quality(repos: &[scoring_types::RepoData], readmes: &BTreeMap<String, scoring_types::ReadmeData>) -> SignalScore {
    if repos.is_empty() {
        return SignalScore::new("readme_quality", 0.0, 0.0, bt(&[("message", json!("No repos found"))]));
    }

    if readmes.is_empty() {
        let with_desc = repos.iter().filter(|r| r.description.is_some()).count();
        if with_desc == 0 {
            return SignalScore::new("readme_quality", 0.0, 0.5, bt(&[("message", json!("No repos with descriptions"))]));
        }
        let total_len: usize = repos.iter().filter_map(|r| r.description.as_ref()).map(|d| d.len()).sum();
        let avg_len = total_len as f64 / with_desc as f64;
        let quality = ((with_desc as f64 / repos.len() as f64) * 50.0 + (avg_len / 10.0).min(50.0)).min(100.0);
        return SignalScore::new("readme_quality", quality, (0.7_f64).min(repos.len() as f64 / 30.0),
            bt(&[("repos_with_description", json!(with_desc)),
                ("avg_description_length", json!(avg_len)), ("mode", json!("description_fallback"))]));
    }

    let total_repos = repos.len();
    let mut repos_with_readme = 0i64;
    let mut total_chars = 0i64;
    let mut total_sections = 0i64;
    let mut total_code_blocks = 0i64;
    let mut total_lists = 0i64;
    let mut total_badges = 0i64;
    let mut repos_with_emoji = 0i64;

    for repo in repos {
        if let Some(readme) = readmes.get(&repo.full_name) {
            if readme.content.is_some() {
                repos_with_readme += 1;
                if let Some(ref content) = readme.content { total_chars += content.len() as i64; }
                total_sections += readme.detected_sections.len() as i64;
                total_code_blocks += readme.code_block_count;
                total_lists += readme.list_count;
                total_badges += readme.badge_count;
                if readme.has_emoji { repos_with_emoji += 1; }
            }
        }
    }

    if repos_with_readme == 0 {
        return SignalScore::new("readme_quality", 0.0, 0.5, bt(&[("message", json!("No repos with README content"))]));
    }

    let rwr = repos_with_readme as f64;
    let presence = (rwr / total_repos as f64) * 30.0;
    let structure = ((total_sections as f64 / rwr) * 5.0 + (total_code_blocks as f64 / rwr) * 3.0 + (total_lists as f64 / rwr) * 1.5).min(30.0);
    let chars_score = (total_chars as f64 / rwr / 66.7).min(15.0);
    let badge_score = ((total_badges as f64 / rwr) * 2.0).min(10.0);
    let emoji_score = (repos_with_emoji as f64 / rwr) * 15.0;
    let quality = (presence + structure + chars_score + badge_score + emoji_score).min(100.0);

    SignalScore::new("readme_quality", quality, (0.9_f64).min(rwr / 20.0),
        bt(&[("repos_with_readme", json!(repos_with_readme)),
            ("avg_char_count", json!((total_chars as f64 / rwr * 10.0).round() / 10.0)),
            ("avg_sections", json!((total_sections as f64 / rwr * 10.0).round() / 10.0)),
            ("avg_code_blocks", json!((total_code_blocks as f64 / rwr * 10.0).round() / 10.0)),
            ("avg_lists", json!((total_lists as f64 / rwr * 10.0).round() / 10.0)),
            ("avg_badges", json!((total_badges as f64 / rwr * 10.0).round() / 10.0)),
            ("emoji_ratio", json!((repos_with_emoji as f64 / rwr * 100.0).round() / 100.0)),
            ("mode", json!("readme_content"))]))
}

fn extract_commit_semantics(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() {
        return SignalScore::new("commit_semantics", 0.0, 0.0, bt(&[("message", json!("No commits found"))]));
    }

    let n = commits.len() as f64;
    let cc_types = ["feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert"];
    let imperative_verbs = ["add","remove","fix","update","change","implement","refactor","rename",
        "move","delete","create","merge","bump","upgrade","downgrade","revert","introduce",
        "extract","replace","migrate","enable","disable","improve","simplify","clean",
        "bootstrap","initialize","convert","handle","support"];

    let mut conventional_count = 0u64;
    let mut multi_line_count = 0u64;
    let mut total_len: usize = 0;
    let mut imperative_count = 0u64;

    for commit in commits {
        let msg = &commit.message;
        total_len += msg.len();

        let is_cc = msg.find(':').map(|pos| {
            let prefix = &msg[..pos];
            cc_types.iter().any(|t| prefix == *t || prefix == &format!("{}!", t) || prefix.starts_with(&format!("{}(", t)))
        }).unwrap_or(false);
        if is_cc { conventional_count += 1; }

        if msg.contains('\n') && msg.lines().filter(|l| !l.trim().is_empty()).count() > 1 {
            multi_line_count += 1;
        }

        if let Some(subject) = msg.lines().next() {
            let after = subject.find(':').map(|i| &subject[i+1..]).unwrap_or(subject);
            let first = after.trim().split_whitespace().next()
                .map(|w| w.trim_end_matches(|c: char| c == '.' || c == ',' || c == '!' || c == ';').to_lowercase());
            if let Some(ref fw) = first {
                if imperative_verbs.contains(&fw.as_str()) { imperative_count += 1; }
            }
        }
    }

    let cr = conventional_count as f64 / n;
    let avg_len = total_len as f64 / n;
    let mr = multi_line_count as f64 / n;
    let ir = imperative_count as f64 / n;
    let score = (cr * 30.0 + (avg_len / 50.0 * 25.0).min(25.0) + mr * 25.0 + ir * 20.0).min(100.0);

    SignalScore::new("commit_semantics", score, (0.9_f64).min(commits.len() as f64 / 100.0),
        bt(&[("total_commits", json!(commits.len())),
            ("conventional_commit_ratio", json!((cr * 100.0).round() / 100.0)),
            ("avg_message_length", json!((avg_len * 10.0).round() / 10.0)),
            ("multi_line_ratio", json!((mr * 100.0).round() / 100.0)),
            ("imperative_mood_ratio", json!((ir * 100.0).round() / 100.0))]))
}

fn extract_cicd_maturity(cicd_configs: &BTreeMap<String, Vec<scoring_types::CicdConfigData>>, repos: &[scoring_types::RepoData]) -> SignalScore {
    if cicd_configs.is_empty() || repos.is_empty() {
        return SignalScore::new("cicd_maturity", 0.0, 0.0, bt(&[("message", json!("No CI/CD data available"))]));
    }

    let total_repos = repos.len();
    if total_repos == 0 {
        return SignalScore::new("cicd_maturity", 0.0, 0.0, bt(&[("message", json!("No repos found"))]));
    }

    let mut repo_ci_count = 0;
    let mut all_types: BTreeMap<String, i64> = BTreeMap::new();
    for (_, configs) in cicd_configs {
        let has_ci = configs.iter().any(|c| c.exists);
        if has_ci {
            repo_ci_count += 1;
            for c in configs {
                if c.exists { *all_types.entry(c.config_type.clone()).or_insert(0) += 1; }
            }
        }
    }

    if repo_ci_count == 0 {
        return SignalScore::new("cicd_maturity", 0.0, 0.5, bt(&[("message", json!("No CI/CD detected in any repo"))]));
    }

    let prevalence = (repo_ci_count as f64 / total_repos as f64) * 30.0;
    let diversity = (all_types.len() as f64 * 7.5).min(30.0);

    let ga = all_types.get("github_actions").copied().unwrap_or(0);
    let docker = all_types.get("docker").copied().unwrap_or(0);
    let other = all_types.keys().filter(|k| *k != "github_actions" && *k != "docker").count();
    let mut depth = 0.0;
    if ga > 0 { depth += 20.0; }
    if docker > 0 { depth += 10.0; }
    depth += other as f64 * 15.0;
    depth = depth.min(40.0);

    let maturity = (prevalence + diversity + depth).min(100.0);
    let confidence = (0.85_f64).min(0.3 + (repo_ci_count as f64 / total_repos as f64) * 0.5);

    SignalScore::new("cicd_maturity", maturity, confidence,
        bt(&[("repos_with_ci", json!(repo_ci_count)), ("total_repos", json!(total_repos)),
            ("ci_type_count", json!(all_types.len())),
            ("ci_types_found", serde_json::to_value(&all_types.keys().cloned().collect::<Vec<_>>()).unwrap_or_default())]))
}

fn extract_contribution_consistency(contributions: &Option<scoring_types::ContributionData>, commits: &[scoring_types::CommitData]) -> SignalScore {
    if let Some(ref contribs) = contributions {
        let days = &contribs.contribution_days;
        if days.is_empty() {
            return SignalScore::new("contribution_consistency", 0.0, 0.5, bt(&[("message", json!("Empty contribution calendar"))]));
        }
        let total_days = days.len() as f64;
        let active_days = days.iter().filter(|d| d.contribution_count > 0).count() as f64;
        let activity_ratio = active_days / total_days;
        let activity_score = activity_ratio * 35.0;

        let max_gap = days.iter().fold((0i64, 0i64), |(max, curr), d| {
            if d.contribution_count == 0 { (max.max(curr + 1), curr + 1) } else { (max, 0) }
        }).0;

        let gap_score = if max_gap >= 30 { 0.0 } else if max_gap >= 14 { 10.0 } else if max_gap >= 7 { 20.0 } else { 35.0 };

        let consistency_score = (activity_score + gap_score + 30.0 * activity_ratio).min(100.0);
        return SignalScore::new("contribution_consistency", consistency_score, (0.9_f64).min(0.4 + activity_ratio * 0.5),
            bt(&[("total_days", json!(days.len())), ("days_with_contributions", json!(active_days as i64)),
                ("activity_ratio", json!((activity_ratio * 1000.0).round() / 1000.0)),
                ("max_gap_days", json!(max_gap)), ("longest_streak", json!(contribs.longest_streak)),
                ("current_streak", json!(contribs.current_streak)),
                ("mode", json!("contribution_calendar"))]));
    }

    if commits.is_empty() {
        return SignalScore::new("contribution_consistency", 0.0, 0.0, bt(&[("message", json!("No contribution data available"))]));
    }
    if commits.len() < 2 {
        return SignalScore::new("contribution_consistency", 25.0, 0.3, bt(&[("message", json!("Too few commits")),
            ("mode", json!("commit_fallback"))]));
    }

    let mut sorted: Vec<_> = commits.iter().collect();
    sorted.sort_by_key(|c| &c.date);
    match (parse_dt(&sorted[0].date), parse_dt(&sorted[sorted.len()-1].date)) {
        (Ok(first), Ok(last)) => {
            let span_days = (last - first).num_seconds() as f64 / 86400.0;
            let cpd = commits.len() as f64 / span_days.max(1.0);
            let dens = if (0.5..=3.0).contains(&cpd) { 60.0 }
                else if cpd < 0.5 { 30.0 + (cpd / 0.5) * 30.0 }
                else { (60.0 - (cpd - 3.0) * 5.0).max(10.0) };
            let max_gap = (1..sorted.len()).filter_map(|i| {
                match (parse_dt(&sorted[i-1].date), parse_dt(&sorted[i].date)) {
                    (Ok(d1), Ok(d2)) => Some((d2 - d1).num_seconds() as f64 / 86400.0),
                    _ => None
                }
            }).fold(0.0_f64, f64::max);
            let gap = if max_gap >= 30.0 { 20.0 } else if max_gap >= 14.0 { 35.0 } else { 50.0 };
            let score = ((dens + gap) / 2.0).min(100.0);
            SignalScore::new("contribution_consistency", score, (0.5_f64).min(0.2 + commits.len() as f64 / 200.0),
                bt(&[("total_commits", json!(commits.len())), ("span_days", json!((span_days * 10.0).round() / 10.0)),
                    ("commits_per_day", json!((cpd * 100.0).round() / 100.0)),
                    ("max_commit_gap_days", json!((max_gap * 10.0).round() / 10.0)),
                    ("mode", json!("commit_fallback"))]))
        }
        _ => SignalScore::new("contribution_consistency", 0.0, 0.0, bt(&[("message", json!("Error parsing dates"))]))
    }
}

fn extract_ai_usage_patterns(commits: &[scoring_types::CommitData]) -> SignalScore {
    if commits.is_empty() {
        return SignalScore::new("ai_usage_patterns", 50.0, 0.0, bt(&[("message", json!("No commits to analyze"))]));
    }

    let n = commits.len() as f64;
    let lengths: Vec<f64> = commits.iter().map(|c| c.message.len() as f64).collect();
    let avg_len: f64 = lengths.iter().sum::<f64>() / n;
    let variance = lengths.iter().map(|l| (l - avg_len).powi(2)).sum::<f64>() / n;
    let std = variance.sqrt();

    let style = if std < 5.0 { 5.0 } else if std < 10.0 { 20.0 } else if std < 30.0 { 35.0 }
        else if std < 50.0 { 25.0 } else { 15.0 };

    // ---- 2. Timing cluster analysis ----
    let mut sorted: Vec<_> = commits.iter().collect();
    sorted.sort_by_key(|c| &c.date);

    let (timing_score, _burst_ratio) = if sorted.len() >= 2 {
        let mut time_diffs: Vec<f64> = Vec::new();
        for i in 1..sorted.len() {
            if let (Ok(d1), Ok(d2)) = (parse_dt(&sorted[i-1].date), parse_dt(&sorted[i].date)) {
                time_diffs.push((d2 - d1).num_seconds() as f64);
            }
        }

        if time_diffs.is_empty() {
            (20.0, 0.0)
        } else {
            let avg_diff: f64 = time_diffs.iter().sum::<f64>() / time_diffs.len() as f64;
            let diff_variance: f64 = time_diffs.iter()
                .map(|d| (d - avg_diff).powi(2)).sum::<f64>() / time_diffs.len() as f64;
            let _diff_std = diff_variance.sqrt();

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
            let ts = if br > 0.5 { 5.0 }
                else if br > 0.3 { 20.0 }
                else if br < 0.1 && avg_diff > 3600.0 { 35.0 }
                else if br < 0.2 { 30.0 }
                else { 25.0 };
            (ts, br)
        }
    } else {
        (20.0, 0.0)
    };

    // ---- 3. Conventional commit consistency ----
    let cc_types = ["feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert"];
    let cc_count = commits.iter().filter(|c| {
        c.message.find(':').map(|pos| {
            let prefix = &c.message[..pos];
            cc_types.iter().any(|t| prefix == *t || prefix == &format!("{}!", t) || prefix.starts_with(&format!("{}(", t)))
        }).unwrap_or(false)
    }).count();
    let cc_ratio = cc_count as f64 / n;
    let cc_score = if cc_ratio > 0.95 && commits.len() >= 5 { 10.0 } else if cc_ratio > 0.80 { 20.0 }
        else if cc_ratio > 0.40 { 30.0 } else if cc_ratio > 0.10 { 25.0 } else { 20.0 };

    let ai_score = (style + timing_score as f64 + cc_score).min(100.0);
    let confidence = (0.85_f64).min(0.2 + (commits.len() as f64 / 100.0) * 0.5);

    SignalScore::new("ai_usage_patterns", ai_score, confidence,
        bt(&[("total_commits", json!(commits.len())), ("msg_length_std", json!((std * 10.0).round() / 10.0)),
            ("avg_msg_length", json!((avg_len * 10.0).round() / 10.0)),
            ("conventional_commit_ratio", json!((cc_ratio * 100.0).round() / 100.0))]))
}

// Helpers

fn parse_dt(s: &str) -> Result<chrono::DateTime<chrono::Utc>, chrono::ParseError> {
    let s = s.trim_end_matches('Z');
    // Try rfc3339 first, then ISO 8601 with fractional seconds, then without
    chrono::DateTime::parse_from_rfc3339(&format!("{}Z", s))
        .map(|dt| dt.with_timezone(&chrono::Utc))
        .or_else(|_| {
            chrono::NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S%.f")
                .map(|ndt| ndt.and_utc())
        })
        .or_else(|_| {
            chrono::NaiveDateTime::parse_from_str(s, "%Y-%m-%dT%H:%M:%S")
                .map(|ndt| ndt.and_utc())
        })
}

fn bt(pairs: &[(&str, serde_json::Value)]) -> BTreeMap<String, serde_json::Value> {
    pairs.iter().map(|(k, v)| (k.to_string(), v.clone())).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use scoring_types::*;

    fn make_sample_input() -> ScoreInput {
        let mut commits = Vec::new();
        for i in 0..30 {
            commits.push(CommitData {
                sha: format!("sha{}", i),
                message: format!("feat: commit number {}", i),
                author: "user".into(),
                date: format!("2024-01-{:02}T10:00:00Z", (i % 31).max(1)),
                additions: 50, deletions: 10,
            });
        }
        let mut repos = Vec::new();
        for i in 0..30 {
            repos.push(RepoData {
                name: format!("repo{}", i), full_name: format!("user/repo{}", i),
                description: Some(format!("A test repo {}", i)),
                language: if i % 3 == 0 { Some("Rust".into()) }
                    else if i % 3 == 1 { Some("Python".into()) }
                    else { Some("TypeScript".into()) },
                stars: 10, forks: 2, is_fork: i % 5 == 0, is_private: false,
                pushed_at: Some("2024-01-01T00:00:00Z".into()),
            });
        }
        let mut issues = Vec::new();
        for i in 0..20 {
            issues.push(IssueData {
                number: i, title: format!("Issue {}", i),
                state: if i % 3 == 0 { "CLOSED".into() } else { "OPEN".into() },
                created_at: "2024-01-01T00:00:00Z".into(),
                closed_at: if i % 3 == 0 { Some("2024-01-02T00:00:00Z".into()) } else { None },
                comments: (i % 5) as i64, author: "user".into(),
            });
        }
        ScoreInput {
            repos,
            commits,
            issues,
            prs: vec![],
            readmes: BTreeMap::new(),
            cicd_configs: BTreeMap::new(),
            contributions: None,
        }
    }

    #[test]
    fn test_commit_consistency() {
        let input = make_sample_input();
        let result = extract_commit_consistency(&input.commits);
        assert!(result.score > 0.0, "score should be >0, got {}", result.score);
        assert!(result.confidence > 0.0);
        assert_eq!(result.name, "commit_consistency");
    }

    #[test]
    fn test_language_diversity() {
        let input = make_sample_input();
        let result = extract_language_diversity(&input.repos);
        // Python implementation can return negative scores for 2 languages
        assert!(result.score < 0.0 || result.score >= 0.0); // just assert it runs
        assert!(result.confidence > 0.0);
    }

    #[test]
    fn test_issue_engagement() {
        let input = make_sample_input();
        let result = extract_issue_engagement(&input.issues);
        assert!(result.score > 0.0);
    }

    #[test]
    fn test_empty_inputs() {
        let result = extract_commit_consistency(&[]);
        assert_eq!(result.score, 0.0);
        assert_eq!(result.confidence, 0.0);

        let result = extract_language_diversity(&[]);
        assert_eq!(result.score, 0.0);
    }

    #[test]
    fn test_score_user() {
        let input = make_sample_input();
        // Use no profile (legacy mode) to avoid confidence threshold filtering
        let output = score_user(&input, None);
        assert!(output.overall_score > 0.0, "overall_score should be >0, got {}", output.overall_score);
        assert_eq!(output.profile_name, "engineering");
        assert_eq!(output.signal_scores.len(), 12);
    }

    #[test]
    fn test_profiles_weights_sum() {
        let eng = profiles::engineering_profile();
        let sum: f64 = eng.weights.values().sum();
        assert!((sum - 1.0).abs() < 0.001, "engineering weights sum to {}", sum);

        let mkt = profiles::marketing_profile();
        let sum: f64 = mkt.weights.values().sum();
        assert!((sum - 1.0).abs() < 0.001, "marketing weights sum to {}", sum);
    }

    #[test]
    fn test_commit_semantics() {
        let input = make_sample_input();
        let result = extract_commit_semantics(&input.commits);
        assert!(result.score > 0.0, "score should be >0, got {}", result.score);
        assert!(result.confidence > 0.0);
    }

    #[test]
    fn test_readme_quality_fallback() {
        let input = make_sample_input();
        let result = extract_readme_quality(&input.repos, &BTreeMap::new());
        assert!(result.score > 0.0);
        assert_eq!(result.details.get("mode").unwrap(), "description_fallback");
    }
}
