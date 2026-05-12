//! Role-adaptive scoring profiles.
//! Mirrors Python scoring/profiles.py

use std::collections::BTreeMap;
// use std::string::ToString;
use std::vec::Vec;
use scoring_types::{RoleProfile, ALL_SIGNALS};

fn build_profile(
    name: &str, display_name: &str, description: &str,
    weights: &[(&str, f64)], thresholds: &[(&str, f64)],
) -> RoleProfile {
    let mut w = BTreeMap::new();
    let mut t = BTreeMap::new();
    for sig in ALL_SIGNALS {
        w.insert(sig.to_string(), 0.0);
        t.insert(sig.to_string(), 0.3);
    }
    for (k, v) in weights { w.insert(k.to_string(), *v); }
    for (k, v) in thresholds { t.insert(k.to_string(), *v); }
    RoleProfile { name: name.into(), display_name: display_name.into(), description: description.into(), weights: w, confidence_thresholds: t }
}

pub fn engineering_profile() -> RoleProfile {
    build_profile("engineering", "Engineering",
        "Default profile for software engineering roles.",
        &[("commit_consistency", 0.12), ("pr_patterns", 0.12), ("commit_semantics", 0.10),
          ("cicd_maturity", 0.10), ("language_diversity", 0.08), ("response_time", 0.08),
          ("review_patterns", 0.08), ("issue_engagement", 0.08), ("readme_quality", 0.06),
          ("project_ownership", 0.06), ("contribution_consistency", 0.06), ("ai_usage_patterns", 0.06)],
        &[("commit_consistency", 0.4), ("pr_patterns", 0.4), ("commit_semantics", 0.4),
          ("cicd_maturity", 0.4), ("language_diversity", 0.4), ("review_patterns", 0.4),
          ("ai_usage_patterns", 0.4)])
}

pub fn marketing_profile() -> RoleProfile {
    build_profile("marketing", "Marketing",
        "Profile for marketing and community-focused roles.",
        &[("readme_quality", 0.20), ("project_ownership", 0.15), ("issue_engagement", 0.15),
          ("review_patterns", 0.10), ("commit_semantics", 0.08), ("response_time", 0.08),
          ("pr_patterns", 0.06), ("language_diversity", 0.06), ("commit_consistency", 0.04),
          ("cicd_maturity", 0.04), ("contribution_consistency", 0.02), ("ai_usage_patterns", 0.02)],
        &[("readme_quality", 0.3), ("project_ownership", 0.3), ("issue_engagement", 0.3),
          ("response_time", 0.3), ("review_patterns", 0.3), ("contribution_consistency", 0.3)])
}

pub fn non_technical_profile() -> RoleProfile {
    build_profile("non-technical", "Non-Technical",
        "Profile for non-technical roles (design, product, management).",
        &[("project_ownership", 0.20), ("issue_engagement", 0.20), ("review_patterns", 0.12),
          ("readme_quality", 0.10), ("response_time", 0.08), ("pr_patterns", 0.08),
          ("language_diversity", 0.06), ("commit_semantics", 0.04), ("commit_consistency", 0.04),
          ("cicd_maturity", 0.03), ("contribution_consistency", 0.03), ("ai_usage_patterns", 0.02)],
        &[("project_ownership", 0.25), ("issue_engagement", 0.25), ("review_patterns", 0.25),
          ("readme_quality", 0.25), ("response_time", 0.25), ("contribution_consistency", 0.25)])
}

pub fn list_profiles() -> Vec<RoleProfile> {
    vec![engineering_profile(), marketing_profile(), non_technical_profile()]
}

pub fn get_profile(name: &str) -> Option<RoleProfile> {
    list_profiles().into_iter().find(|p| p.name == name)
}

pub fn resolve_role_profile(role: Option<&str>) -> RoleProfile {
    role.and_then(get_profile).unwrap_or_else(engineering_profile)
}
