fn main() {
    let args: Vec<String> = std::env::args().collect();
    let input: scoring_types::ScoreInput = if args.len() > 1 && args[1] == "--input" && args.len() > 2 {
        let path = &args[2];
        let data = std::fs::read_to_string(path).expect("Failed to read input file");
        serde_json::from_str(&data).expect("Failed to parse ScoreInput JSON")
    } else {
        // Read from stdin
        let mut buf = String::new();
        use std::io::Read;
        std::io::stdin().read_to_string(&mut buf).expect("Failed to read stdin");
        serde_json::from_str(&buf).expect("Failed to parse ScoreInput JSON from stdin")
    };

    let role = if args.len() > 3 && args[3] == "--role" && args.len() > 4 {
        Some(args[4].as_str())
    } else {
        None
    };

    let output = scoring_core::engine::score_user(&input, role);
    let json = serde_json::to_string_pretty(&output).expect("Failed to serialize output");
    println!("{}", json);
}
