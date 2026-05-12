//! SP1 zkVM guest program: proves the GitHub fingerprint scoring function.
//!
//! Reads a serialized ScoreInput from the prover's stdin,
//! runs the scoring engine, commits the output hash to the
//! public output stream, and writes the full output to stdout.
#![no_std]
#![no_main]

extern crate alloc;

use alloc::string::ToString;
use serde_json;
use sp1_zkvm::io;

fn main() {
    // Read ScoreInput as JSON from stdin (sent by the host)
    let input_json = io::read::<String>();
    let input: scoring_sp1_core::ScoreInput =
        serde_json::from_str(&input_json).expect("Failed to parse ScoreInput JSON");

    // Run the scoring engine
    let output = scoring_sp1_core::score_user(&input, None);

    // Serialize output
    let output_json =
        serde_json::to_string(&output).expect("Failed to serialize ScoreOutput");

    // Commit the output to the public output stream
    // (This is what gets proven on-chain)
    io::commit(output_json.as_bytes());

    // Also write full output to stdout for the host script to capture
    io::write(&output_json);
}
