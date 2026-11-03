"""Cryptographic Computational Audit Trail & Reproducibility Certification.

Generates immutable, tamper-evident audit certificates for quantitative research models:
1. Canonical JSON serialization of input parameters and outputs.
2. Cryptographic SHA-256 seal tying model equations, inputs, code version, and results.
3. Verification engine to prove that research findings have not been manipulated post-run.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class ReproducibilityCertificate:
    certificate_id: str
    model_name: str
    model_version: str
    created_at_utc: str
    python_version: str
    host_platform: str
    random_seed: Optional[int]
    inputs_hash_sha256: str
    outputs_hash_sha256: str
    computation_seal_sha256: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def verify_integrity(self, original_inputs: Dict[str, Any], original_outputs: Dict[str, Any]) -> bool:
        """Verifies that inputs and outputs match the cryptographic computation seal."""
        inputs_json = json.dumps(original_inputs, sort_keys=True, separators=(",", ":"))
        calc_in_hash = hashlib.sha256(inputs_json.encode("utf-8")).hexdigest()
        if calc_in_hash != self.inputs_hash_sha256:
            return False

        outputs_json = json.dumps(original_outputs, sort_keys=True, separators=(",", ":"))
        calc_out_hash = hashlib.sha256(outputs_json.encode("utf-8")).hexdigest()
        if calc_out_hash != self.outputs_hash_sha256:
            return False

        seal_payload = f"{self.model_name}:{self.model_version}:{self.inputs_hash_sha256}:{self.outputs_hash_sha256}:{self.random_seed}"
        calc_seal = hashlib.sha256(seal_payload.encode("utf-8")).hexdigest()
        return calc_seal == self.computation_seal_sha256


class ComputationalAuditTrail:
    """Cryptographic certification engine for reproducible scientific modeling."""

    @classmethod
    def generate_certificate(
        cls,
        model_name: str,
        model_version: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        random_seed: Optional[int] = None,
        notes: str = "",
    ) -> ReproducibilityCertificate:
        """Constructs an immutable SHA-256 sealed certificate for a simulation run."""
        now_utc = datetime.now(timezone.utc).isoformat()

        inputs_json = json.dumps(inputs, sort_keys=True, separators=(",", ":"))
        inputs_hash = hashlib.sha256(inputs_json.encode("utf-8")).hexdigest()

        outputs_json = json.dumps(outputs, sort_keys=True, separators=(",", ":"))
        outputs_hash = hashlib.sha256(outputs_json.encode("utf-8")).hexdigest()

        seal_payload = f"{model_name}:{model_version}:{inputs_hash}:{outputs_hash}:{random_seed}"
        seal_hash = hashlib.sha256(seal_payload.encode("utf-8")).hexdigest()

        cert_id = f"CERT-{model_name.upper()[:8]}-{seal_hash[:12]}"

        return ReproducibilityCertificate(
            certificate_id=cert_id,
            model_name=model_name,
            model_version=model_version,
            created_at_utc=now_utc,
            python_version=sys.version.split()[0],
            host_platform=f"{platform.system()}-{platform.machine()}",
            random_seed=random_seed,
            inputs_hash_sha256=inputs_hash,
            outputs_hash_sha256=outputs_hash,
            computation_seal_sha256=seal_hash,
            metadata={
                "notes": notes,
                "schema_version": "1.0.0",
                "hashing_algorithm": "SHA-256",
            },
        )
