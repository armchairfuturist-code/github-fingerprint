//! Prover CLI wrapper called by the Python Celery worker.
//! Reads ScoreInput JSON from stdin, runs SP1 proof generation,
//! writes proof metadata to stdout.
//!
//! Usage: echo '<score_input_json>' | scoring-prover-cli
//!        scoring-prover-cli --input <file.json>

use std::io::Read;
use std::process::{Command, Stdio};
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    // Read ScoreInput
    let input_json: String = if args.len() > 1 && args[1] == "--input" && args.len() > 2 {
        std::fs::read_to_string(&args[2]).expect("Failed to read input file")
    } else {
        let mut buf = String::new();
        std::io::stdin().read_to_string(&mut buf).expect("Failed to read stdin");
        buf
    };

    // Validate JSON
    let _input: serde_json::Value = serde_json::from_str(&input_json)
        .expect("Invalid ScoreInput JSON");

    let start = Instant::now();

    // Run SP1 script via subprocess
    // TODO: in production, replace with direct library call
    let sp1_script = std::env::var("SP1_SCRIPT_PATH")
        .unwrap_or_else(|_| "scoring-sp1-script".to_string());

    let input_path = std::env::temp_dir().join("prover_input.json");
    std::fs::write(&input_path, &input_json).expect("Failed to write temp input");

    let status = Command::new(&sp1_script)
        .args(&["--input", &input_path.to_string_lossy()])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .status()
        .expect("Failed to run SP1 script");

    let elapsed = start.elapsed();

    if !status.success() {
        eprintln!("SP1 script failed with exit code: {:?}", status.code());
        std::process::exit(1);
    }

    // Output proof metadata as JSON
    let metadata = serde_json::json!({
        "status": "proof_generated",
        "proving_time_ms": elapsed.as_millis(),
        "proving_time_seconds": elapsed.as_secs_f64(),
        "input_path": input_path.to_string_lossy().to_string(),
        "prover": std::env::var("SP1_PROVER").unwrap_or_else(|_| "local".to_string()),
    });

    println!("{}", serde_json::to_string_pretty(&metadata).unwrap());
}
