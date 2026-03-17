# FamilyPulse-II
[![Ask DeepWiki](https://devin.ai/assets/askdeepwiki.png)](https://deepwiki.com/AshrayaBashyal/FamilyPulse-II)

FamilyPulse-II is a comprehensive, multi-hospital home-healthcare coordination platform. Built with Django and Django REST Framework, it serves as the backend for a system designed to connect hospitals, healthcare staff, and patients (via their guardians) to manage in-home medical visits seamlessly.

The platform provides a robust, role-based system to handle everything from hospital registration and staff management to patient care, visit scheduling, dynamic reporting, and detailed analytics.

## Core Features

-   **Multi-Role Authentication**: A secure JWT-based authentication system supports multiple user roles with distinct permissions:
    -   **Superadmin**: Manages the entire platform, approves new hospitals, and views system-wide analytics.
    -   **Hospital Admin**: Manages a specific hospital, its staff, visit types, and report templates.
    -   **Medical Admin**: Reviews and approves/rejects clinical reports submitted by nurses.
    -   **Nurse**: Accepts visit assignments, conducts in-home visits, and submits detailed reports.
    -   **Guardian**: Manages dependents, books visits, and tracks their health progress.

-   **Hospital & Staff Management**:
    -   Superadmin can approve, suspend, or activate hospitals on the platform.
    -   Hospital Admins can invite and manage their staff (Nurses, Medical Admins), assigning them roles within the hospital.

-   **Dependent & Guardian Management**:
    -   Guardians can create profiles for their dependents, detailing their medical history, allergies, and other critical information.
    -   Guardians can delegate access by inviting other users to become guardians for a dependent.

-   **Advanced Visit Lifecycle**: A sophisticated state machine governs the entire lifecycle of a home visit:
    1.  **Request**: A guardian books a visit for a dependent, selecting a hospital and visit type.
    2.  **Schedule**: A hospital admin sets a specific time for the visit.
    3.  **Guardian Confirmation**: The guardian receives the proposed time and must either confirm or cancel. The visit is auto-confirmed if a response deadline passes.
    4.  **Assignment**: The admin assigns an available nurse to the confirmed visit.
    5.  **Accept/Reject**: The nurse can accept or reject the assignment. If rejected, the visit returns to the scheduling pool.
    6.  **Execution**: The nurse starts and completes the on-site visit.
    7.  **Reporting**: A report is submitted by the nurse.
    8.  **Review**: A medical admin approves or rejects the report, completing the visit cycle.

-   **Dynamic Reporting System**:
    -   Hospital admins can create custom, dynamic report templates for each type of visit (e.g., 'Wound Care', 'Vitals Check').
    -   Templates consist of configurable fields (text, number, choice, etc.), ensuring structured and consistent data collection.
    -   Nurses fill out reports based on these templates post-visit.
    -   All reports are versioned, providing a complete audit trail of submissions and reviews.

-   **Role-Specific Analytics Engine**:
    -   **Superadmin Dashboard**: Platform-wide metrics on hospitals, users, visits, and revenue.
    -   **Hospital Admin Dashboard**: In-depth analytics on visit volume, nurse performance, and report statuses for their hospital.
    -   **Medical Admin Dashboard**: Metrics on report review times and approval/rejection rates.
    -   **Nurse Dashboard**: Personal statistics on completed visits and report statuses.
    -   **Guardian Dashboard**: Health trends and visit history for their dependents, tracked via data from approved reports.

## Tech Stack

-   **Backend**: Django, Django REST Framework
-   **Database**: PostgreSQL
-   **Authentication**: REST Framework Simple JWT (Access/Refresh Tokens)
-   **API Documentation**: `drf-spectacular` for generating OpenAPI 3 schemas with Swagger UI and Redoc.

## Project Structure

The project is organized into modular Django apps, each responsible for a distinct domain of the platform:

-   `apps/accounts`: User registration, authentication, and profile management.
-   `apps/hospitals`: Hospital registration, staff memberships, and role management.
-   `apps/dependents`: Dependent profiles and guardianship management.
-   `apps/visits`: The core visit lifecycle, including scheduling, assignment, and state transitions.
-   `apps/reports`: Dynamic report templates, report creation, and the review process.
-   `apps/analytics`: Data aggregation and service layer for all analytics endpoints.
-   `apps/payments`: (Stub) Integration with payment gateways like Stripe.
-   `apps/notifications`: (Stub) Infrastructure for sending emails and other notifications.
-   `common`: Shared utilities, base models, and custom permissions.

## Getting Started

To run the project locally, follow these steps.

### Prerequisites

-   Python 3.10+
-   PostgreSQL

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/AshrayaBashyal/FamilyPulse-II.git
    cd FamilyPulse-II
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate
    # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    -   Create a `.env` file in the project root by copying the example file:
        ```sh
        cp .env.example .env
        ```
    -   Edit the `.env` file and set the required variables:
        ```
        SECRET_KEY=<your-super-secret-key>
        DATABASE_URL=postgres://<user>:<password>@<host>:<port>/<dbname>
        ```

5.  **Run database migrations:**
    ```sh
    python manage.py migrate
    ```

6.  **Create a superuser (for platform admin access):**
    ```sh
    python manage.py createsuperuser
    ```

7.  **Run the development server:**
    ```sh
    python manage.py runserver
    ```
    The API will be available at `http://127.0.0.1:8000`.

## API Documentation

The API is self-documented using `drf-spectacular`. Once the server is running, you can access the interactive API documentation at:

-   **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
-   **Redoc**: `http://127.0.0.1:8000/api/redoc/`