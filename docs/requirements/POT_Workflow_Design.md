# Patient Onboarding Team Member (POT) Workflow Design

**Document Version:** 1.0  
**Last Updated:** January 17, 2025  
**Author:** System Design Team  
**Purpose:** Comprehensive workflow design for Patient Onboarding Team Members with ZEN Medical Onboarding (ZMO) integration

---

## Executive Summary

This document outlines the detailed workflow design for Patient Onboarding Team Members (POTs) within the ZEN Medical system. POTs serve as the critical first point of contact in the patient care pipeline, responsible for patient intake, eligibility verification, documentation collection, and preparation for provider assignment.

**Key Features:**
- ZEN Medical Onboarding (ZMO) checklist-based workflow
- Patient eligibility verification and insurance management
- EMed chart creation and facility assignment
- Medical records collection and routing
- Initial assessment and provider assignment preparation
- Integration with PCPM and PCCM assignment workflows

---

## Role Definition and Responsibilities

### 1.1 POT Core Functions

**Primary Responsibilities:**
- **Patient Intake:** Initial patient registration and demographic data collection
- **Insurance Verification:** Verify patient insurance coverage and eligibility status
- **Documentation Collection:** Gather required medical records and referral documentation
- **Chart Creation:** Create patient charts in EMed system with proper facility assignment
- **Initial Assessment:** Conduct preliminary patient needs assessment
- **Workflow Preparation:** Prepare patient data for PCPM provider assignment
- **Status Tracking:** Maintain patient onboarding status throughout the process

### 1.2 Patient Onboarding Pipeline Position

**POT Position in Onboarding Workflow:**
```
Referral Intake → POT Patient Processing → Eligibility Verification → Chart Creation → PCPM Initial TV → Provider Assignment
```

**POT Specific Tasks:**
1. **Patient Registration:** Add patient information to Patient Care Database
2. **Eligibility Check:** Verify patient insurance and eligibility status
3. **Chart Creation:** Create patient chart in EMed with facility assignment
4. **Intake Processing:** Perform patient intake including referral and medical records
5. **TV Scheduling & Provider Assignment:** Schedule Initial TV and assign regional provider

---

## ZMO Workflow Structure

### 2.1 ZMO Checklist Overview

**ZMO System Features:**
- Left-to-right checklist workflow for patient onboarding
- Status tracking with trigger-based progression
- Integration with EMed for chart creation
- Communication interface for referral sources
- Patient analytics and reporting dashboard

**Core ZMO Columns (POT Responsibility):**
- Patient Status
- Patient Demographics (Name, DOB, Contact Info)
- Address and Geographic Information
- Facility Assignment
- Insurance Information
- Eligibility Verification
- EMed Chart Creation Status
- Prescreen Call Notes
- Medical Records Routing

### 2.2 POT Workflow Stages

#### Stage 1: Patient Registration
**Data Collection:**
```javascript
const PatientRegistration = {
    patientStatus: String,        // "Active", "Inactive", "Deceased"
    patientName: String,          // "LAST, FIRST"
    lastName: String,
    firstName: String,
    dateOfBirth: Date,
    contactName: String,          // Emergency contact
    phone: String,
    address: {
        street: String,
        city: String,
        state: String,
        zipCode: String
    },
    facility: String,             // Assigned facility
    emedFacility: String,         // EMed facility assignment
    representatives: Array,       // Facility representatives
    addToMap: Boolean,           // Geographic mapping flag
    insurance: {
        primary: String,
        policyNumber: String
    },
    region: String               // Geographic region assignment
};
```

#### Stage 2: Eligibility Verification
**Verification Process:**
- Insurance coverage verification
- Benefit eligibility confirmation
- Prior authorization requirements
- Coverage limitations and restrictions
- Medicare/Medicaid coordination

**Status Tracking:**
```javascript
const EligibilityStatus = {
    trigger: String,              // "Elig (Done-NextList)", "Still working"
    status: String,               // "TRUE", "FALSE", "Pending"
    list: String,                 // Current processing list
    eligibilityNotes: String,     // Detailed verification notes
    verificationDate: Date,
    verifiedBy: String           // POT member who verified
};
```

#### Stage 3: Chart Creation
**EMed Integration:**
- Create patient chart in EMed system
- Assign appropriate facility
- Set up patient demographics
- Configure access permissions
- Link insurance information

**Chart Creation Tracking:**
```javascript
const ChartCreation = {
    emedChartCreated: Boolean,    // "Y"/"N"
    chartId: String,              // EMed chart identifier
    facilityAssignment: String,   // Assigned EMed facility
    creationDate: Date,
    createdBy: String,           // POT member
    chartStatus: String          // "Active", "Pending", "Error"
};
```

#### Stage 4: Intake Processing
**Documentation Collection:**
- Referral documentation
- Medical records requests
- Insurance cards and documentation
- Emergency contact information
- Care preferences and directives

**Intake Form Management:**
```javascript
const IntakeProcessing = {
    prescreenCall: {
        completed: Boolean,
        notes: String,
        callDate: Date,
        outcome: String          // "Completed", "Unreachable", "Rescheduled"
    },
    emedIntakeForm: Boolean,     // "Y"/"N"
    medicalRecords: {
        requested: Boolean,
        received: Boolean,
        routingNotes: String,
        routingDate: Date
    },
    referralDocuments: {
        received: Boolean,
        complete: Boolean,
        notes: String
    }
};
```

#### Stage 5: Initial TV Scheduling
**Provider Manager Coordination:**
- Schedule Initial TV with PCPM
- Coordinate patient availability
- Prepare patient file for handoff
- Update scheduling system

**Scheduling Management:**
```javascript
const InitialTVScheduling = {
    initialTVDate: Date,
    scheduledProvider: String,    // PCPM assigned
    schedulingNotes: String,
    patientNotified: Boolean,
    confirmationStatus: String,   // "Confirmed", "Pending", "Rescheduled"
    handoffComplete: Boolean
};
```

---

## POT Dashboard Interface

### 3.1 Main Dashboard

**Dashboard Components:**
- **Active Queue:** Patients currently in POT processing
- **Daily Metrics:** Intake volume, completion rates, pending items
- **Status Overview:** Patients by processing stage
- **Alert Center:** Urgent items requiring attention

**Queue Management:**
```javascript
const POTDashboard = {
    activeQueue: {
        newReferrals: Number,
        eligibilityPending: Number,
        chartCreationPending: Number,
        intakeInProgress: Number,
        schedulingPending: Number,
        readyForHandoff: Number
    },
    dailyMetrics: {
        newIntakes: Number,
        completedProcessing: Number,
        eligibilityVerified: Number,
        chartsCreated: Number,
        scheduledTVs: Number
    },
    alerts: {
        urgentEligibility: Array,
        overdueIntakes: Array,
        schedulingConflicts: Array,
        systemErrors: Array
    }
};
```

### 3.2 Patient Processing Interface

**Individual Patient View:**
- Patient demographic information
- Processing checklist with status indicators
- Notes and communication history
- Document upload and management
- Status update controls

**Processing Checklist:**
```javascript
const ProcessingChecklist = {
    patientRegistration: {
        status: String,           // "Pending", "In Progress", "Complete"
        completedBy: String,
        completedDate: Date,
        notes: String
    },
    eligibilityVerification: {
        status: String,
        verificationMethod: String,
        insuranceConfirmed: Boolean,
        benefitsVerified: Boolean,
        notes: String
    },
    chartCreation: {
        status: String,
        emedChartId: String,
        facilityAssigned: String,
        creationDate: Date
    },
    intakeProcessing: {
        status: String,
        prescreenCompleted: Boolean,
        documentsCollected: Boolean,
        medicalRecordsRequested: Boolean,
        notes: String
    },
    tvScheduling: {
        status: String,
        scheduledDate: Date,
        assignedPCPM: String,
        patientNotified: Boolean
    }
};
```

---

## Integration with Existing Workflows

### 4.1 System Integration Points

**EMed Integration:**
- Chart creation API
- Patient demographic updates
- Facility assignment management
- Access permission configuration

**Insurance Verification Systems:**
- Real-time eligibility checking
- Benefit verification
- Prior authorization tracking
- Coverage limitation alerts

**Communication Systems:**
- Patient notification system
- Provider scheduling integration
- Referral source communication
- Internal team messaging

---

## Quality Assurance and Compliance

### 5.1 Data Accuracy Standards

**Verification Requirements:**
- Double-entry verification for critical data
- Insurance information validation
- Address and contact verification
- Medical record completeness checks

**Quality Metrics:**
- Data accuracy rate: >99%
- Eligibility verification accuracy: >98%
- Chart creation success rate: >99%
- Processing time compliance: >95%

### 5.2 Compliance Monitoring

**HIPAA Compliance:**
- Patient information security
- Access logging and monitoring
- Communication encryption
- Document handling protocols

**Regulatory Requirements:**
- Insurance verification standards
- Medical record handling
- Patient consent management
- Audit trail maintenance

---

## Performance Metrics and Reporting

### 6.1 POT Performance Indicators

**Efficiency Metrics:**
- Average processing time per patient: Target <4 hours
- Eligibility verification time: Target <30 minutes
- Chart creation time: Target <15 minutes
- Daily intake capacity: Target 15-20 patients

**Quality Metrics:**
- Data accuracy rate
- Eligibility verification accuracy
- Chart creation success rate
- Patient satisfaction with intake process

**Productivity Metrics:**
- Patients processed per day
- Processing stage completion rates
- Handoff success rate to PCPM
- System utilization efficiency

### 6.2 Reporting Dashboard

**Daily Reports:**
- Intake volume and completion
- Processing stage status
- Quality metrics summary
- Alert and exception reports

**Weekly Reports:**
- Trend analysis
- Performance comparisons
- Quality assurance summary
- Process improvement recommendations

**Monthly Reports:**
- Comprehensive performance analysis
- Compliance audit results
- System optimization recommendations
- Training needs assessment

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Weeks 1-2)
- ZMO system setup and configuration
- Patient registration database
- Basic eligibility verification integration
- EMed chart creation API integration

### Phase 2: Workflow Implementation (Weeks 3-4)
- POT dashboard development
- Patient processing interface
- Status tracking and checklist system
- Basic reporting functionality

### Phase 3: Integration and Automation (Weeks 5-6)
- PCPM handoff workflow
- Automated eligibility verification
- Communication system integration
- Advanced reporting and analytics

### Phase 4: Quality Assurance (Weeks 7-8)
- Quality control mechanisms
- Compliance monitoring tools
- Performance tracking systems
- User training and documentation

### Phase 5: Testing and Deployment (Weeks 9-10)
- User acceptance testing
- Performance optimization
- Security audit and compliance verification
- Production deployment and monitoring

---

## Success Criteria

### 6.1 Operational Excellence
- **Processing Efficiency:** >95% of patients processed within target timeframes
- **Data Quality:** >99% accuracy in patient registration and eligibility verification
- **System Integration:** Seamless handoff to PCPM workflow with <1% error rate
- **User Satisfaction:** >4.5/5 rating from POT team members

### 6.2 Patient Experience
- **Intake Experience:** >4.0/5 patient satisfaction rating
- **Communication:** Clear and timely updates throughout onboarding process
- **Accessibility:** Multiple communication channels and language support
- **Efficiency:** Reduced time from referral to provider assignment

### 6.3 Compliance and Security
- **HIPAA Compliance:** 100% compliance with patient privacy regulations
- **Data Security:** Zero security incidents or data breaches
- **Audit Readiness:** Complete audit trails for all patient interactions
- **Regulatory Compliance:** Full compliance with healthcare regulations

---

## Conclusion

The POT workflow design provides a comprehensive framework for efficient patient onboarding within the ZEN Medical system. By implementing this structured approach, the organization can ensure consistent, high-quality patient intake processes while maintaining compliance and preparing patients for seamless transition to provider care.

The integration with existing workflows (PCPM, PCCM) and systems (EMed, insurance verification) creates a cohesive patient care pipeline that maximizes efficiency and minimizes errors in the critical onboarding phase.

**Next Steps:**
1. Review and approve POT workflow design
2. Finalize ZMO system requirements
3. Begin Phase 1 implementation
4. Develop POT training materials
5. Establish performance monitoring systems