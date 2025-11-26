// RRS Validator - Rwanda Report System Smart Contract
// Anchors evidence hashes on Cardano blockchain for tamper-proof reporting

validator RRSValidator {
  datum: Datum
  redeemer: Redeemer
  context: ScriptContext
}

type Datum {
  report_id: ByteArray
  evidence_hash: ByteArray
  timestamp: Int
  category: ByteArray
  is_anonymous: Bool
}

type Redeemer {
  Anchor: AnchorParams
  Verify: VerifyParams
  Update: UpdateParams
}

type AnchorParams {
  report_id: ByteArray
  evidence_hash: ByteArray
  category: ByteArray
  is_anonymous: Bool
}

type VerifyParams {
  report_id: ByteArray
  evidence_hash: ByteArray
}

type UpdateParams {
  report_id: ByteArray
  new_evidence_hash: ByteArray
}

// -------------------------------
// MAIN VALIDATION LOGIC
// -------------------------------
func validate(datum: Datum, redeemer: Redeemer, context: ScriptContext) -> Bool {
  when redeemer is {
    Anchor(params) -> validate_anchor(params, context)
    Verify(params) -> validate_verify(params, datum)
    Update(params) -> validate_update(params, datum, context)
  }
}

// -------------------------------
// ANCHOR VALIDATION
// -------------------------------
func validate_anchor(params: AnchorParams, context: ScriptContext) -> Bool {
  let tx_info = context.transaction
  let outputs = tx_info.outputs
  let own_address = context.script_address

  let contract_outputs = list.filter(outputs, fn(output) { output.address == own_address })

  if list.length(contract_outputs) != 1 {
    False
  } else {
    let output = list.head(contract_outputs)
    when output.datum is {
      Some(d) -> when d is {
        Inline(datum_value) -> validate_new_datum(datum_value, params)
        _ -> False
      }
      None -> False
    }
  }
}

func validate_new_datum(datum: Datum, params: AnchorParams) -> Bool {
  // Delegate core validation to lib.ak
  lib.validate_anchor_params(
    datum.report_id,
    datum.evidence_hash,
    datum.category,
    datum.timestamp,
    0,              // current_time simplified for hackathon
    datum.is_anonymous
  )
    && datum.report_id == params.report_id
    && datum.evidence_hash == params.evidence_hash
    && datum.category == params.category
    && datum.is_anonymous == params.is_anonymous
}

// -------------------------------
// VERIFY EXISTING REPORT
// -------------------------------
func validate_verify(params: VerifyParams, datum: Datum) -> Bool {
  lib.validate_verify_params(params.report_id, params.evidence_hash)
    && params.report_id == datum.report_id
    && params.evidence_hash == datum.evidence_hash
}

// -------------------------------
// UPDATE EXISTING REPORT
// -------------------------------
func validate_update(params: UpdateParams, datum: Datum, context: ScriptContext) -> Bool {
  // Only allow updates for same report, simplified timing
  params.report_id == datum.report_id
    && validate_update_timing(datum.timestamp)
}

func validate_update_timing(original_timestamp: Int) -> Bool {
  // Hackathon simplified timing
  True
}

// -------------------------------
// UTILITY
// -------------------------------
func string_to_bytes(str: String) -> ByteArray {
  []
}
