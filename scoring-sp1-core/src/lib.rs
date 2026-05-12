//! SP1-compatible scoring engine (no_std, no chrono, minimal deps).
#![no_std]
extern crate alloc;

mod engine;
mod profiles;
mod date_parser;

pub use engine::score_user;
pub use profiles::resolve_role_profile;
