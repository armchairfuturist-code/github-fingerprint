---
depends_on: [M004]
---

# M005: Matchmaking & Notifications (DRAFT)

**Status:** Draft — refine before executing

## Seed Material

### Architecture
- **Matching:** Automated candidate-role matching based on signal profiles and recruiter requirements
- **Notifications:** Recruiter interest → candidate notified via GitHub (issue/notification API) and/or email
- **Passive discovery:** Thesis is great candidates aren't actively looking — notification is the connection point

### Key Decisions (from M001 discussion)
- GitHub notifications are the primary channel (issue comment on a designated repo, or GitHub notifications API)
- Email as fallback
- Candidates control opt-in status per recruiter/role
- No cold outreach — candidate must opt in to be discoverable

### Provisional Slices
- S01: Matchmaking & Notifications — Automated matching engine + notification delivery via GitHub API and email fallback. Opt-in control for candidates.

### Open Questions
- How does a recruiter "express interest"? Button on profile? Message system?
- How is the matching algorithm weighted? What's the scoring formula for match quality?
- How do we prevent spam/abuse of the notification system?
- Does the notification create a GitHub issue on a repo the candidate owns, or use the GitHub Notifications API directly?
- Do we need an in-platform messaging system, or is GitHub notification + email sufficient?
