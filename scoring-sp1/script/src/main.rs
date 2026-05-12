//! SP1 host script: runs the prover on a scoring input.
//!
//! Usage: cargo run --release -- --input <score_input.json>
//!
//! Reads a ScoreInput JSON file, sends it to the SP1 guest program,
//! receives the proven output, and prints proof metadata.
use std::path::PathBuf;
use std::fs;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    let input_path = if args.len() > 1 && args[1] == "--input" && args.len() > 2 {
        PathBuf::from(&args[2])
    } else {
        eprintln!("Usage: scoring-sp1-script --input <score_input.json>");
        std::process::exit(1);
    };

    // Read input
    let input_json = fs::read_to_string(&input_path)
        .expect("Failed to read input file");

    // Verify it's valid JSON
    let _input: serde_json::Value = serde_json::from_str(&input_json)
        .expect("Invalid JSON input");

    println!("[sp1-script] Loaded input from: {}", input_path.display());

    // Set up SP1 prover
    // Uses SP1_PROVER env var: "local" for CPU proving, "network" for Succinct's network
    let prover = std::env::var("SP1_PROVER").unwrap_or_else(|_| "local".to_string());

    // The ELF binary path. When built with `cargo prove build`, the ELF
    // is at: program/elf/riscv32im-succinct-zkvm-elf
    let elf_path = PathBuf::from(
        std::env::var("SP1_ELF_PATH")
            .unwrap_or_else(|_| "program/elf/riscv32im-succinct-zkvm-elf".to_string()),
    );
    let elf = fs::read(&elf_path).expect("ELF file not found. Run `cargo prove build` first.");

    println!("[sp1-script] ELF size: {} bytes", elf.len());
    println!("[sp1-script] Prover mode: {}", prover);

    // Generate proof
    // Use SP1 SDK's ProverClient
    let client = sp1_sdk::ProverClient::new();
    let (pk, vk) = client.setup(elf);

    // Create proof
    let proof_result = client.prove(&pk, &input_json).expect("Proof generation failed");

    println!("[sp1-script] Proof generated successfully!");
    println!("[sp1-script] Proof size: {} bytes", proof_result.bytes().len());
    println!("[sp1-script] Cycle count: {}", proof_result.cycle_count());
    println!("[sp1-script] Public output: {}", String::from_utf8_lossy(&proof_result.public_values()));

    // Save proof to file
    let output_proof_path = PathBuf::from(
        std::env::var("SP1_PROOF_OUTPUT")
            .unwrap_or_else(|_| "proof.bin".to_string()),
    );

    // Verify proof locally (quick sanity check)
    client.verify(&proof_result, &vk).expect("Proof verification failed");
    println!("[sp1-script] Proof verification: PASSED");

    // Serialize proof (SP1ProofWithVKey) to disk for contract submission
    let proof_bytes = bincode::serialize(&proof_result).expect("Failed to serialize proof");
    fs::write(&output_proof_path, &proof_bytes).expect("Failed to write proof file");
    println!("[sp1-script] Proof saved to: {}", output_proof_path.display());

    println!("[sp1-script] Done!");
}
