# MyHealthTeam - Streamlit Healthcare Workflow Management

A comprehensive healthcare workflow management system built with Streamlit, designed to streamline patient care coordination, provider management, and healthcare administration.

## 🏥 Overview

MyHealthTeam is a web-based healthcare management platform that provides role-based dashboards for different healthcare professionals and administrators. The system manages patient care workflows, provider tasks, billing coordination, and administrative oversight.

## 🚀 Features

### Role-Based Dashboards
- **Admin Dashboard**: Complete system oversight, user management, and system analytics
- **Care Provider Dashboard**: Patient management, task tracking, and care coordination
- **Care Coordinator Dashboard**: Patient assignment, workflow coordination, and billing management
- **Lead Coordinator Dashboard**: Team oversight and performance monitoring
- **Data Entry Dashboard**: Patient data input and management
- **Onboarding Dashboard**: New patient and provider onboarding workflows

### Key Capabilities
- Patient care workflow automation
- Provider task management and tracking
- Monthly and weekly performance summaries
- Billing coordination and tracking
- Regional provider management
- ZIP code-based patient assignment
- Comprehensive reporting and analytics

## 🛠 Technology Stack

- **Frontend**: Streamlit
- **Database**: SQLite
- **Backend**: Python
- **Data Visualization**: Plotly, Matplotlib
- **Data Processing**: Pandas, NumPy

## 📁 Project Structure

```
├── app.py                          # Main Streamlit application
├── src/
│   ├── database.py                 # Database connection and utilities
│   ├── dashboards/                 # Role-based dashboard modules
│   │   ├── admin_dashboard.py
│   │   ├── care_coordinator_dashboard_enhanced.py
│   │   ├── care_provider_dashboard_enhanced.py
│   │   ├── data_entry_dashboard.py
│   │   ├── lead_coordinator_dashboard.py
│   │   └── onboarding_dashboard.py
│   ├── utils/                      # Utility functions and components
│   └── sql/                        # SQL queries and scripts
├── docs/                           # Documentation and requirements
├── sql/                           # Database schema and setup scripts
└── _do_not_use_old_scripts/       # Legacy scripts (archived)
```

## 🏃‍♂️ Getting Started

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/creative-adventures/myhealthteam.git
cd myhealthteam
```

2. Install required packages:
```bash
pip install streamlit pandas plotly sqlite3 numpy matplotlib
```

3. Run the application:
```bash
streamlit run app.py
```

4. Access the application at `http://localhost:8501`

## 📊 Database Schema

The application uses SQLite with the following key tables:
- `users` - User authentication and role management
- `patients` - Patient information and status
- `providers` - Healthcare provider details
- `coordinators` - Care coordinator information
- `tasks` - Task management and tracking
- `monthly_summaries` - Performance and billing summaries
- `regions` - Geographic region management

## 🔒 User Roles

1. **Admin**: Full system access and management
2. **Care Provider**: Patient care and task management
3. **Care Coordinator**: Patient assignment and coordination
4. **Lead Coordinator**: Team oversight and management
5. **Data Entry**: Patient data input and updates

## 📝 Documentation

Comprehensive documentation is available in the `docs/` directory:
- System architecture and design
- Workflow specifications
- API documentation
- Deployment guides

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Built with ❤️ for healthcare professionals**