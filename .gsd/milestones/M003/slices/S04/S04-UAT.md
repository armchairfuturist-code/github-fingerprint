# S04: ZK Proof Viewer & Badge — UAT

**Milestone:** M003
**Written:** 2026-05-15T05:43:57.400Z

# S04 UAT — ZK Proof Viewer & Badge

## Proof badge renders correct status text
- [ ] Badge shows "Not Started" with bullet symbol for unknown status
- [ ] Badge shows "Pending" with white circle symbol for pending status
- [ ] Badge shows "Generating ..." with medium circle symbol for proof_generating status
- [ ] Badge shows "Proof Ready" with checkmark symbol for proof_generated status
- [ ] Badge shows "On Chain" with square symbol for on_chain status
- [ ] Badge shows "Failed" with X mark symbol for failed status

## Expandable proof viewer shows metadata
- [ ] Proof ID displayed when available
- [ ] Created and Updated timestamps displayed in readable format
- [ ] Tx Hash displayed when on_chain
- [ ] Error message displayed when failed
- [ ] Proof Path displayed when available
- [ ] Verifying Contract displayed when on_chain (with metadata populated)

## Graceful degradation
- [ ] Template shows "Not Started" / "unknown" when no proof record exists
- [ ] No proof detail rows rendered when proof_id is None

## Copy button
- [ ] Copy Proof Data button present with copyProofData handler
- [ ] data-proof attribute contains serialized proof JSON
- [ ] No shell-redirect artifacts in rendered HTML

## Regression
- [ ] Profile page still returns 200 for valid usernames
- [ ] Profile page still returns 404 for nonexistent usernames
- [ ] Cache-Control header still present
- [ ] Attestation badge still renders correctly
- [ ] Score breakdown bars still render
