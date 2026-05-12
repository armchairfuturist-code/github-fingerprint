//! Simplified ISO 8601 date parser for no_std environments.
//! Parses "2024-01-01T10:00:00Z" and similar to Unix timestamps (seconds).

/// Parse an ISO 8601 UTC timestamp string to seconds since Unix epoch.
/// Supports formats:
///   - "2024-01-01T10:00:00Z"
///   - "2024-01-01T10:00:00.123Z"
///   - "2024-01-01T10:00:00.123456Z"
pub fn parse_timestamp(s: &str) -> Option<i64> {
    let s = s.trim_end_matches('Z');
    if s.len() < 19 {
        return None;
    }

    // Parse components
    let year: i64 = s[0..4].parse().ok()?;
    let month: u32 = s[5..7].parse().ok()?;
    let day: u32 = s[8..10].parse().ok()?;
    let hour: u32 = s[11..13].parse().ok()?;
    let min: u32 = s[14..16].parse().ok()?;
    let sec: u32 = s[17..19].parse().ok()?;

    // Days since epoch for the date
    let days = days_since_epoch(year, month, day)?;
    let total_secs = days * 86400 + (hour as i64 * 3600 + min as i64 * 60 + sec as i64);
    Some(total_secs)
}

/// Compute difference in seconds between two ISO 8601 timestamps.
pub fn timestamp_diff_seconds(a: &str, b: &str) -> Option<f64> {
    let ta = parse_timestamp(a)?;
    let tb = parse_timestamp(b)?;
    Some((ta - tb) as f64)
}

/// Days since Unix epoch (1970-01-01).
fn days_since_epoch(year: i64, month: u32, day: u32) -> Option<i64> {
    if month < 1 || month > 12 || day < 1 || day > 31 {
        return None;
    }

    // Days from 1970-01-01 to year-01-01
    let y = year - 1;
    let days_to_year = y * 365 + y / 4 - y / 100 + y / 400 - 719162; // days from 1970

    // Days from year-01-01 to year-month-day
    let days_in_months: [i64; 12] = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    let is_leap = (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);

    let mut day_of_year: i64 = 0;
    for m in 1..month {
        if m == 2 && is_leap {
            day_of_year += 29;
        } else {
            day_of_year += days_in_months[(m - 1) as usize];
        }
    }
    day_of_year += day as i64 - 1;

    Some(days_to_year + day_of_year)
}
