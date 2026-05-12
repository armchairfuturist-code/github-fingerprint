// SPDX-License-Identifier: MIT
/// @notice Standard SP1 verifier interface for Groth16 proofs.
/// @dev Matches the canonical ISP1Verifier used by SP1's `cargo prove deploy`.
pragma solidity ^0.8.20;

interface ISP1Verifier {
    /// @notice Verify a Groth16 proof.
    /// @param programVKey The verification key for the SP1 program.
    /// @param publicValues The public values (output) committed by the zkVM program.
    /// @param proofBytes The serialized Groth16 proof (points + public inputs).
    /// @custom:revert InvalidProof if the proof does not verify.
    function verifyProof(
        bytes32 programVKey,
        bytes calldata publicValues,
        bytes calldata proofBytes
    ) external view;
}
