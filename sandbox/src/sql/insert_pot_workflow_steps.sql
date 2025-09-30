-- Insert workflow steps for POT_PATIENT_ONBOARDING (template_id = 14)
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES -- Stage 1: Patient Registration
    (
        14,
        1,
        'Collect patient demographics',
        'POT',
        'Complete patient basic information form',
        'Day1'
    ),
    (
        14,
        2,
        'Collect address and contact information',
        'POT',
        'Complete address and emergency contact details',
        'Day1'
    ),
    (
        14,
        3,
        'Collect referral information',
        'POT',
        'Complete referral source and provider details',
        'Day1'
    ),
    -- Stage 2: Eligibility Verification
    (
        14,
        4,
        'Verify insurance coverage',
        'POT',
        'Verify patient insurance eligibility',
        'Day1'
    ),
    (
        14,
        5,
        'Record eligibility status',
        'POT',
        'Document eligibility verification result',
        'Day1'
    ),
    (
        14,
        6,
        'Document eligibility notes',
        'POT',
        'Record any eligibility issues or notes',
        'Day1'
    ),
    -- Stage 3: Chart Creation
    (
        14,
        7,
        'Create EMed chart (manual verification)',
        'POT',
        'Create patient chart in EMed system',
        'Day1'
    ),
    (
        14,
        8,
        'Assign facility in system',
        'POT',
        'Assign patient to appropriate facility',
        'Day1'
    ),
    (
        14,
        9,
        'Confirm chart creation complete',
        'POT',
        'Verify chart creation and facility assignment',
        'Day1'
    ),
    -- Stage 4: Intake Processing
    (
        14,
        10,
        'Request medical records',
        'POT',
        'Send medical records request to referring provider',
        'Day2'
    ),
    (
        14,
        11,
        'Collect referral documents',
        'POT',
        'Collect and verify referral documentation',
        'Day2'
    ),
    (
        14,
        12,
        'Complete prescreen call',
        'POT',
        'Conduct initial patient prescreen call',
        'Day2'
    ),
    (
        14,
        13,
        'Document received materials',
        'POT',
        'Document all received materials and status',
        'Day3'
    ),
    -- Stage 5: TV Scheduling & Handoff
    (
        14,
        14,
        'Schedule Initial TV with PCPM',
        'POT',
        'Schedule telehealth visit with provider manager',
        'Day3'
    ),
    (
        14,
        15,
        'Notify patient of TV appointment',
        'POT',
        'Send appointment confirmation to patient',
        'Day3'
    ),
    (
        14,
        16,
        'Prepare handoff documentation',
        'POT',
        'Prepare complete patient file for handoff',
        'Day3'
    ),
    (
        14,
        17,
        'Complete handoff to PCPM',
        'POT',
        'Transfer patient to PCPM for provider assignment',
        'Day3'
    );