//! scoring-cross-compare: feeds identical ScoreInput fixtures to both scoring engines
//! and reports exact diffs per signal. Exits 0 if all PASS, 1 on any FAIL.

use std::path::PathBuf;
use std::process;

use clap::Parser;
use scoring_types::ScoreOutput;

#[derive(Parser)]
#[command(name = "scoring-cross-compare", about = "Compare scoring-core and scoring-sp1-core outputs")]
struct Args {
    /// Path to a single fixture JSON file
    #[arg(long)]
    fixture: Option<PathBuf>,

    /// Scan py-scoring-ref/fixtures/*.json for all fixtures
    #[arg(long)]
    all_fixtures: bool,
}

fn main() {
    let args = Args::parse();

    let fixture_paths: Vec<PathBuf> = if let Some(path) = &args.fixture {
        vec![path.clone()]
    } else if args.all_fixtures {
        let fixtures_dir = PathBuf::from("py-scoring-ref/fixtures");
        let mut paths: Vec<_> = std::fs::read_dir(&fixtures_dir)
            .unwrap_or_else(|e| {
                eprintln!("ERROR: cannot read fixtures dir {:?}: {}", fixtures_dir, e);
                process::exit(1);
            })
            .filter_map(|entry| {
                let entry = entry.ok()?;
                let path = entry.path();
                if path.extension().map(|e| e == "json").unwrap_or(false) {
                    Some(path)
                } else {
                    None
                }
            })
            .collect();
        paths.sort();
        paths
    } else {
        eprintln!("ERROR: specify --fixture <path> or --all-fixtures");
        process::exit(1);
    };

    if fixture_paths.is_empty() {
        eprintln!("ERROR: no fixture files found");
        process::exit(1);
    }

    let mut any_failed = false;

    for path in &fixture_paths {
        let fixture_name = path.file_stem().unwrap_or_default().to_string_lossy();
        println!("\n=== Fixture: {} ===\n", fixture_name);

        let json_str = match std::fs::read_to_string(path) {
            Ok(s) => s,
            Err(e) => {
                eprintln!("ERROR: cannot read {:?}: {}", path, e);
                any_failed = true;
                continue;
            }
        };

        let input: scoring_types::ScoreInput = match serde_json::from_str(&json_str) {
            Ok(i) => i,
            Err(e) => {
                eprintln!("ERROR: cannot parse {:?}: {}", path, e);
                any_failed = true;
                continue;
            }
        };

        let reference = scoring_core::engine::score_user(&input, None);
        let test = scoring_sp1_core::score_user(&input, None);

        let fixture_failed = compare_outputs(&reference, &test);
        if fixture_failed {
            any_failed = true;
        }
    }

    if any_failed {
        println!("\n❌ Some fixtures have differences (exit 1)");
        process::exit(1);
    } else {
        println!("\n✅ All fixtures match perfectly (exit 0)");
    }
}

/// Compare two ScoreOutputs. Returns true if any diff found.
fn compare_outputs(reference: &ScoreOutput, test: &ScoreOutput) -> bool {
    let mut any_diff = false;

    // --- overall_score ---
    any_diff |= compare_f64("overall_score", reference.overall_score, test.overall_score);

    // --- profile_name ---
    if reference.profile_name != test.profile_name {
        println!("FAIL  profile_name");
        println!("      reference: {:?}", reference.profile_name);
        println!("      test:      {:?}", test.profile_name);
        any_diff = true;
    } else {
        println!("PASS  profile_name");
    }

    // --- signals_scored ---
    if reference.signals_scored != test.signals_scored {
        println!("FAIL  signals_scored");
        println!("      reference: {:?}", reference.signals_scored);
        println!("      test:      {:?}", test.signals_scored);
        any_diff = true;
    } else {
        println!("PASS  signals_scored");
    }

    // --- signal_scores (per-signal comparison) ---
    let all_signal_names: std::collections::BTreeSet<&str> = reference
        .signal_scores
        .keys()
        .chain(test.signal_scores.keys())
        .map(|s| s.as_str())
        .collect();

    // Sort for deterministic output
    let mut sorted_names: Vec<&&str> = all_signal_names.iter().collect();
    sorted_names.sort();

    for &&name in &sorted_names {
        let ref_sig = reference.signal_scores.get(name);
        let test_sig = test.signal_scores.get(name);

        match (ref_sig, test_sig) {
            (Some(ref_r), Some(ref_t)) => {
                let mut sig_diff = false;

                sig_diff |= compare_f64_detail("score", &format!("{}/score", name), ref_r.score, ref_t.score);
                sig_diff |= compare_f64_detail("confidence", &format!("{}/confidence", name), ref_r.confidence, ref_t.confidence);

                if ref_r.details != ref_t.details {
                    // Find specific detail differences
                    let mut detail_diff = false;
                    let all_detail_keys: std::collections::BTreeSet<&str> = ref_r
                        .details
                        .keys()
                        .chain(ref_t.details.keys())
                        .map(|s| s.as_str())
                        .collect();
                    for &dk in &all_detail_keys {
                        let ref_v = ref_r.details.get(dk);
                        let test_v = ref_t.details.get(dk);
                        if ref_v != test_v {
                            println!("FAIL  {}/details/{}", name, dk);
                            println!("      reference: {:?}", ref_v);
                            println!("      test:      {:?}", test_v);
                            detail_diff = true;
                        }
                    }
                    if !detail_diff {
                        // Keys match but value comparison shows diff — print full details map
                        println!("FAIL  {}/details", name);
                        println!("      reference: {:?}", ref_r.details);
                        println!("      test:      {:?}", ref_t.details);
                    }
                    sig_diff = true;
                }

                if !sig_diff {
                    println!("PASS  {}", name);
                } else {
                    any_diff = true;
                }
            }
            (Some(_), None) => {
                println!("FAIL  {}  (missing in SP1 engine)", name);
                any_diff = true;
            }
            (None, Some(_)) => {
                println!("FAIL  {}  (extra in SP1 engine)", name);
                any_diff = true;
            }
            (None, None) => {}
        }
    }

    // --- signals_below_threshold ---
    if reference.signals_below_threshold != test.signals_below_threshold {
        println!("FAIL  signals_below_threshold");
        println!("      reference: {:?}", reference.signals_below_threshold);
        println!("      test:      {:?}", test.signals_below_threshold);
        any_diff = true;
    } else {
        println!("PASS  signals_below_threshold");
    }

    // --- risk_flags ---
    if reference.risk_flags != test.risk_flags {
        println!("FAIL  risk_flags");
        println!("      reference: {:?}", reference.risk_flags);
        println!("      test:      {:?}", test.risk_flags);
        any_diff = true;
    } else {
        println!("PASS  risk_flags");
    }

    any_diff
}

/// Compare f64 with exact equality. Returns true if different.
fn compare_f64(label: &str, ref_v: f64, test_v: f64) -> bool {
    if ref_v != test_v {
        println!("FAIL  {}", label);
        println!("      reference: {:?}", ref_v);
        println!("      test:      {:?}", test_v);
        true
    } else {
        println!("PASS  {}", label);
        false
    }
}

/// Compare f64 with exact equality, printing detail prefix.
fn compare_f64_detail(label: &str, path: &str, ref_v: f64, test_v: f64) -> bool {
    if ref_v != test_v {
        println!("FAIL  {}", path);
        println!("      reference {}: {:?}", label, ref_v);
        println!("      test {}:      {:?}", label, test_v);
        true
    } else {
        false
    }
}
