//! Shared data types for the GitHub fingerprint scoring pipeline.
//! Supports both std and no_std+alloc modes via feature flags.

#![cfg_attr(not(feature = "std"), no_std)]

#[cfg(not(feature = "std"))]
extern crate alloc;

#[cfg(feature = "std")]
use std::collections::BTreeMap;
#[cfg(not(feature = "std"))]
use alloc::collections::BTreeMap;
#[cfg(not(feature = "std"))]
use alloc::string::{String, ToString};
#[cfg(not(feature = "std"))]
use alloc::vec::Vec;

use serde::{Deserialize, Serialize};

/// Input data for the scoring engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoreInput {
    pub repos: Vec<RepoData>,
    pub commits: Vec<CommitData>,
    pub issues: Vec<IssueData>,
    pub prs: Vec<PrData>,
    #[serde(default)]
    pub readmes: BTreeMap<String, ReadmeData>,
    #[serde(default)]
    pub cicd_configs: BTreeMap<String, Vec<CicdConfigData>>,
    pub contributions: Option<ContributionData>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepoData {
    pub name: String,
    pub full_name: String,
    pub description: Option<String>,
    pub language: Option<String>,
    pub stars: i64,
    pub forks: i64,
    pub is_fork: bool,
    pub is_private: bool,
    pub pushed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommitData {
    pub sha: String,
    pub message: String,
    pub author: String,
    pub date: String,
    pub additions: i64,
    pub deletions: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IssueData {
    pub number: i64,
    pub title: String,
    pub state: String,
    pub created_at: String,
    pub closed_at: Option<String>,
    pub comments: i64,
    pub author: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PrData {
    pub number: i64,
    pub title: String,
    pub state: String,
    pub created_at: String,
    pub closed_at: Option<String>,
    pub merged_at: Option<String>,
    pub additions: i64,
    pub deletions: i64,
    pub changed_files: i64,
    pub comments: i64,
    pub review_comments: i64,
    pub author: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReadmeData {
    pub content: Option<String>,
    pub size_bytes: i64,
    pub encoding: String,
    pub name: String,
    #[serde(default)]
    pub detected_sections: Vec<String>,
    #[serde(default)]
    pub badge_count: i64,
    #[serde(default)]
    pub has_code_blocks: bool,
    #[serde(default)]
    pub code_block_count: i64,
    #[serde(default)]
    pub has_emoji: bool,
    #[serde(default)]
    pub list_count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CicdConfigData {
    pub path: String,
    pub config_type: String,
    pub exists: bool,
    #[serde(default)]
    pub size_bytes: i64,
    #[serde(default)]
    pub content_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionData {
    pub total_contributions: i64,
    #[serde(default)]
    pub contribution_years: Vec<i64>,
    #[serde(default)]
    pub contribution_days: Vec<ContributionDay>,
    #[serde(default)]
    pub weeks_with_contributions: i64,
    #[serde(default)]
    pub total_weeks: i64,
    pub first_contribution_date: Option<String>,
    #[serde(default)]
    pub longest_streak: i64,
    #[serde(default)]
    pub current_streak: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContributionDay {
    pub date: String,
    pub contribution_count: i64,
}

/// Result of a single signal extraction.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignalScore {
    pub name: String,
    pub score: f64,
    pub confidence: f64,
    pub details: BTreeMap<String, serde_json::Value>,
}

impl SignalScore {
    pub fn new(name: &str, score: f64, confidence: f64, details: BTreeMap<String, serde_json::Value>) -> Self {
        Self { name: name.to_string(), score, confidence, details }
    }
}

/// Output from the scoring engine.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoreOutput {
    pub overall_score: f64,
    pub signal_scores: BTreeMap<String, SignalScore>,
    pub risk_flags: Vec<String>,
    pub profile_name: String,
    pub signals_below_threshold: Vec<String>,
    pub signals_scored: usize,
}

/// Role profile configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RoleProfile {
    pub name: String,
    pub display_name: String,
    pub description: String,
    pub weights: BTreeMap<String, f64>,
    pub confidence_thresholds: BTreeMap<String, f64>,
}

/// All known signal names.
pub const ALL_SIGNALS: &[&str] = &[
    "commit_consistency", "pr_patterns", "commit_semantics", "cicd_maturity",
    "language_diversity", "response_time", "review_patterns", "issue_engagement",
    "readme_quality", "project_ownership", "contribution_consistency", "ai_usage_patterns",
];
