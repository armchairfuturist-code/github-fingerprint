// SPDX-License-Identifier: MIT
/// @title SP1Verifier
/// @notice Deployable SP1 Groth16 verifier for Base Sepolia.
/// @dev    Verifies SP1 zkVM Groth16 proofs over BN254.
///         Single assembly block prevents Solidity stack-too-deep.
pragma solidity ^0.8.20;

import {ISP1Verifier} from "./ISP1Verifier.sol";

contract SP1Verifier is ISP1Verifier {
    uint256 private constant Q = 21888242871839275222246405745257275088548364400416034343698204186575808495617;

    mapping(bytes32 => bytes) public vkeyRegistry;

    event VKeyRegistered(bytes32 indexed programVKey, uint256 numIcPoints);

    function registerVKey(bytes32 programVKey, bytes calldata vkData) external {
        require(vkData.length >= 448, "VKey data too short");
        require(vkeyRegistry[programVKey].length == 0, "VKey already registered");
        vkeyRegistry[programVKey] = vkData;
        emit VKeyRegistered(programVKey, (vkData.length - 448) / 64 + 1);
    }

    function isVKeyRegistered(bytes32 programVKey) external view returns (bool) {
        return vkeyRegistry[programVKey].length > 0;
    }

    /// @inheritdoc ISP1Verifier
    function verifyProof(
        bytes32 programVKey,
        bytes calldata,
        bytes calldata proofBytes
    ) external view override {
        require(proofBytes.length >= 256, "Proof too short");
        require((proofBytes.length - 256) % 32 == 0, "Bad public input alignment");

        bytes memory vkData = vkeyRegistry[programVKey];
        require(vkData.length >= 448, "VKey not registered");

        // Single assembly block — reads proof + VKey, computes pi_ic via precompiles,
        // encodes 4 pairings, and calls ECPAIRING precompile.
        assembly {
            // ── Decode proof into memory at 0x80-0x160 ──
            let pptr := proofBytes.offset
            for { let j := 0 } lt(j, 8) { j := add(j, 1) } {
                let coord := calldataload(add(pptr, mul(j, 0x20)))
                if iszero(lt(coord, Q)) { revert(0, 0) }
                mstore(add(0x80, mul(j, 0x20)), coord)
            }

            // ── Decode VKey into memory at 0x180-0x360 ──
            let vptr := add(vkData, 0x20)
            for { let j := 0 } lt(j, 14) { j := add(j, 1) } {
                mstore(add(0x180, mul(j, 0x20)), mload(add(vptr, mul(j, 0x20))))
            }
            // ic[0] at vptr + 0x1c0
            mstore(0x340, mload(add(vptr, 0x1c0)))
            mstore(0x360, mload(add(vptr, 0x1e0)))

            // ── Count public inputs ──
            let npub := div(sub(proofBytes.length, 256), 32)

            // ── Compute pi_ic ──
            let piX := mload(0x340)
            let piY := mload(0x360)

            for { let i := 0 } lt(i, npub) { i := add(i, 1) } {
                let pub := calldataload(add(add(proofBytes.offset, 0x100), mul(i, 0x20)))
                if iszero(pub) { continue }

                // ic[i+1] at vptr + 0x1e0 + (i+1)*64
                let icPtr := add(vptr, add(0x1e0, mul(add(i, 1), 0x40)))
                let icX := mload(icPtr)
                let icY := mload(add(icPtr, 0x20))

                // ECMUL: pub * icX,icY via precompile 0x07
                // Input layout at scratch: icX(32) icY(32) pub(32) = 0x60 bytes
                mstore(0x00, icX)
                mstore(0x20, icY)
                mstore(0x40, pub)

                let ms := staticcall(gas(), 0x07, 0x00, 0x60, 0x380, 0x40)
                if iszero(and(ms, eq(returndatasize(), 0x40))) { revert(0, 0) }

                let mulX := mload(0x380)
                let mulY := mload(0x3a0)

                // ECADD: pi += mul via precompile 0x06
                mstore(0x00, piX)
                mstore(0x20, piY)
                mstore(0x40, mulX)
                mstore(0x60, mulY)

                let as_ := staticcall(gas(), 0x06, 0x00, 0x80, 0x380, 0x40)
                if iszero(and(as_, eq(returndatasize(), 0x40))) { revert(0, 0) }

                piX := mload(0x380)
                piY := mload(0x3a0)
            }

            // ── Negate points ──
            let negAY  := sub(Q, mload(0x1a0))
            let negPiY := sub(Q, piY)
            let negCY  := sub(Q, mload(0x160))

            // ── Allocate pairing input (768 bytes + 32 length) ──
            let freePtr := mload(0x40)
            mstore(freePtr, 0x300)
            let p := add(freePtr, 0x20)

            // Pair 1: e(A, B)
            mstore(add(p, 0x000), mload(0x80))
            mstore(add(p, 0x020), mload(0xa0))
            mstore(add(p, 0x040), mload(0xc0))
            mstore(add(p, 0x060), mload(0xe0))
            mstore(add(p, 0x080), mload(0x100))
            mstore(add(p, 0x0a0), mload(0x120))
            // Pair 2: e(-α, β)
            mstore(add(p, 0x0c0), mload(0x180))
            mstore(add(p, 0x0e0), negAY)
            mstore(add(p, 0x100), mload(0x1c0))
            mstore(add(p, 0x120), mload(0x1e0))
            mstore(add(p, 0x140), mload(0x200))
            mstore(add(p, 0x160), mload(0x220))
            // Pair 3: e(-π, γ)
            mstore(add(p, 0x180), piX)
            mstore(add(p, 0x1a0), negPiY)
            mstore(add(p, 0x1c0), mload(0x240))
            mstore(add(p, 0x1e0), mload(0x260))
            mstore(add(p, 0x200), mload(0x280))
            mstore(add(p, 0x220), mload(0x2a0))
            // Pair 4: e(-C, δ)
            mstore(add(p, 0x240), mload(0x140))
            mstore(add(p, 0x260), negCY)
            mstore(add(p, 0x280), mload(0x2c0))
            mstore(add(p, 0x2a0), mload(0x2e0))
            mstore(add(p, 0x2c0), mload(0x300))
            mstore(add(p, 0x2e0), mload(0x320))

            mstore(0x40, add(freePtr, 0x340))

            // ── ECPAIRING precompile (0x08) ──
            let ss := staticcall(gas(), 0x08, p, 0x300, 0x00, 0x20)
            if iszero(ss) { revert(0, 0) }

            if iszero(eq(mload(0x00), 1)) { revert(0, 0) }
        }
    }
}
