# LearnMetrics AI
### AI-Powered Teaching Assistant & Student Engagement Platform

LearnMetrics AI is an intelligent educational platform designed to enhance teaching and learning through Artificial Intelligence, Retrieval-Augmented Generation (RAG), document management, and student engagement analytics.

The platform enables teachers to manage and publish academic resources, interact with AI-powered document intelligence, and monitor student engagement. Students can access learning materials and interact with an AI Teaching Assistant that generates context-aware responses based on uploaded academic documents.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [AI Teaching Assistant](#ai-teaching-assistant)
- [Document Management](#document-management)
- [Document Engagement Analytics](#document-engagement-analytics)
- [User Roles](#user-roles)
- [Project Structure](#project-structure)
- [Database Architecture](#database-architecture)
- [Installation and Setup](#installation-and-setup)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Traditional educational platforms primarily provide static learning resources and limited interaction between students and academic content.

LearnMetrics AI addresses this limitation by combining document intelligence with conversational AI and engagement monitoring.

The platform provides:

- AI-powered question answering using uploaded academic materials.
- Retrieval-Augmented Generation for context-aware responses.
- Centralized academic document management.
- Teacher-controlled document publishing.
- Student document access and engagement tracking.
- Teacher dashboards for monitoring document engagement.
- Role-based access control for administrators, teachers, and students.
- Structured academic data management.

The objective is to create a more interactive, accessible, and data-informed educational environment.

---

## Key Features

### 1. AI Teaching Assistant

An intelligent conversational assistant that helps students understand academic concepts using institution-provided learning materials.

Features:

- Context-aware question answering.
- Retrieval-Augmented Generation (RAG).
- Document-based information retrieval.
- Semantic vector search.
- Conversation management.
- Chat history.
- Contextual responses based on indexed academic resources.

### 2. Teacher AI Document Studio

A centralized workspace for teachers to manage academic documents and learning resources.

Features:

- Upload and manage academic documents.
- Organize educational resources.
- Process documents for AI-based retrieval.
- Publish learning materials for students.
- Manage document availability.
- Monitor document engagement.

### 3. Document Engagement Analytics

Provides teachers with insights into how students interact with published learning materials.

Features:

- Document preview tracking.
- Separate download tracking.
- Total document views.
- Unique student counts.
- Repeat view tracking.
- Student-level engagement information.
- Last-viewed timestamps.
- Teacher-level document engagement reports.

The analytics distinguish between document previews and downloads to provide a clearer understanding of student interaction.

### 4. Role-Based Dashboards

Dedicated interfaces provide access to relevant functionality according to user roles.

**Administrator**
- Manage platform users.
- Manage academic structure.
- Oversee platform operations.
- Manage role-based access.

**Teacher**
- Manage academic documents.
- Publish learning resources.
- Access Teacher AI Document Studio.
- Monitor document engagement.
- View student interaction details.
- Use academic dashboards.

**Student**
- Access published learning materials.
- Interact with the AI Teaching Assistant.
- Manage conversations.
- Access available academic resources.

### 5. Academic Management

The platform provides structured academic data management through:

- Institutions.
- Departments.
- Courses.
- Semesters.
- Subjects.
- Student enrollments.
- Teacher profiles.
- Teaching assignments.

---

## System Architecture

LearnMetrics AI follows a modular Django architecture that separates application responsibilities into independent components.

```mermaid
flowchart TD
    A[Users] --> B[Presentation Layer]
    B --> C[Django Application Layer]

    C --> D[Authentication & Authorization]
    C --> E[Academic Management]
    C --> F[Document Management]
    C --> G[AI Teaching Assistant]
    C --> H[Engagement Analytics]
    C --> I[Dashboards]

    F --> J[Document Processing]
    J --> K[Text Extraction & Chunking]
    K --> L[Embedding Generation]
    L --> M[PostgreSQL + pgvector]

    G --> N[Query Processing]
    N --> O[Semantic Retrieval]
    O --> M
    O --> P[LLM Generation]
    P --> Q[Context-Aware Response]

    H --> R[Engagement Records]
    R --> S[Analytics & Reporting]
```

### Architectural Components

| Layer | Responsibility |
|---|---|
| Presentation | Django Templates, HTML, CSS, Bootstrap and JavaScript |
| Application | Django views, services, selectors and business logic |
| Authentication | User authentication and role-based permissions |
| Academic | Academic entities and enrollment management |
| Document | Upload, processing, publishing and access management |
| AI | Retrieval-Augmented Generation and conversational AI |
| Vector Database | Embedding storage and similarity search |
| Analytics | Document engagement tracking and reporting |
| Database | Persistent relational and vector data storage |

---

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Django |
| Database | PostgreSQL |
| Vector Search | pgvector |
| AI Architecture | Retrieval-Augmented Generation (RAG) |
| Embeddings | Sentence Transformers / configured embedding provider |
| LLM Integration | Configurable LLM provider |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5 |
| Database Features | JSONB, UUIDs, PostgreSQL indexes |
| Version Control | Git, GitHub |
| Development Tools | VS Code, pgAdmin |

---

## AI Teaching Assistant

The AI Teaching Assistant uses Retrieval-Augmented Generation to provide responses grounded in uploaded academic materials.

### RAG Pipeline

**1. Document Ingestion**

Teachers upload academic resources through the document management interface.

**2. Text Extraction**

The system extracts textual content from supported documents.

**3. Text Chunking**

Extracted content is divided into smaller chunks to improve retrieval precision.

**4. Embedding Generation**

Text chunks are converted into vector embeddings using the configured embedding model.

**5. Vector Storage**

Embeddings and associated metadata are stored in PostgreSQL using pgvector.

**6. Query Processing**

Students submit questions through the conversational interface.

**7. Semantic Retrieval**

The system converts the query into an embedding and retrieves relevant document chunks using vector similarity search.

**8. Context-Aware Generation**

Retrieved information is supplied to the configured language model to generate a relevant response.

### RAG Workflow

```mermaid
flowchart TD
    A[Teacher Uploads Document] --> B[Document Extraction]
    B --> C[Text Chunking]
    C --> D[Embedding Generation]
    D --> E[PostgreSQL + pgvector]

    F[Student Question] --> G[Query Embedding]
    G --> H[Vector Similarity Search]
    E --> H
    H --> I[Relevant Context]
    I --> J[LLM]
    J --> K[Generated Response]
    K --> L[Student Chat Interface]
```

---

## Document Management

The document management module provides a controlled environment for academic resource distribution.

The workflow includes:

1. Teachers upload academic documents.
2. Documents are processed and indexed where applicable.
3. Teachers manage publication and availability.
4. Students access authorized published documents.
5. Document interactions are recorded for engagement analytics.

Document permissions ensure that students access only resources made available to them.

---

## Document Engagement Analytics

Document engagement analytics help teachers understand student interaction with academic resources.

### Tracked Metrics

| Metric | Description |
|---|---|
| Total Views | Total recorded document preview events |
| Unique Students | Number of distinct students who viewed a document |
| Repeat Views | Additional preview events from previously recorded students |
| Downloads | Number of recorded download events |
| Last Viewed | Most recent recorded student interaction |

### Engagement Tracking Workflow

```mermaid
flowchart TD
    A[Student Opens Document] --> B{Interaction Type}
    B -->|Preview| C[Record Preview Event]
    B -->|Download| D[Record Download Event]

    C --> E[Update Engagement Metrics]
    D --> E

    E --> F[Teacher Analytics Dashboard]
    F --> G[Document-Level Statistics]
    F --> H[Student-Level Details]
```

Preview events and download events are tracked separately to avoid treating every document interaction as the same activity.

---

## User Roles

The platform supports three primary user roles.

| Role | Access |
|---|---|
| Administrator | Platform administration, user management and academic structure |
| Teacher | Academic documents, publishing, AI Document Studio and engagement analytics |
| Student | Published learning materials and AI Teaching Assistant |

Role-based authorization ensures that users can access only the functionality permitted by their assigned role.

---

## Project Structure

The application follows a modular Django project structure.

```text
LearnMetricsAi/
│
├── apps/
│   ├── accounts/
│   ├── academics/
│   ├── students/
│   ├── teachers/
│   ├── documents/
│   ├── rag/
│   ├── dashboard/
│   └── core/
│
├── config/
│   └── settings/
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│
├── requirements.txt
├── manage.py
├── .env.example
├── .gitignore
└── README.md
```

*Note: This structure represents the application's main architectural organization. Individual subdirectories and settings files may vary in the repository.*

---

## Database Architecture

LearnMetrics AI uses PostgreSQL as its primary relational database.

The database supports:

- UUID-based identifiers where configured.
- Foreign-key relationships.
- JSONB fields where required.
- Database indexing.
- Relational integrity.
- Vector embedding storage through pgvector.

### Core Academic Relationships

```mermaid
erDiagram
    USER ||--o| STUDENT : has
    USER ||--o| TEACHER : has

    INSTITUTION ||--o{ DEPARTMENT : contains
    DEPARTMENT ||--o{ COURSE : offers
    COURSE ||--o{ SEMESTER : contains
    SEMESTER ||--o{ SUBJECT : includes

    STUDENT ||--o{ STUDENT_ENROLLMENT : has
    COURSE ||--o{ STUDENT_ENROLLMENT : enrolls
    SEMESTER ||--o{ STUDENT_ENROLLMENT : belongs_to

    TEACHER ||--o{ TEACHING_ASSIGNMENT : receives
    SUBJECT ||--o{ TEACHING_ASSIGNMENT : assigned_to

    USER ||--o{ DOCUMENT : manages
    DOCUMENT ||--o{ DOCUMENT_ENGAGEMENT : records
```

---

## Installation and Setup

### Prerequisites

Ensure that the following software is installed:

- Python 3.12 or compatible project-supported version.
- PostgreSQL.
- pgvector PostgreSQL extension.
- Git.
- pip.
- Virtual environment support.

### 1. Clone the Repository

```bash
git clone https://github.com/ChaitanyaCodec/LearnMetricsAi.git

cd LearnMetricsAi
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv

.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip

pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a PostgreSQL database and ensure pgvector is available.

```sql
CREATE DATABASE learnmetrics_ai;
```

Enable the vector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Configure the database connection using the environment variables expected by the project's Django settings.

### 5. Configure Environment Variables

Create a `.env` file using the project's `.env.example` as a reference.

Typical configuration includes:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True

DATABASE_URL=postgresql://username:password@localhost:5432/learnmetrics_ai

# Configure the AI provider credentials
# according to the selected provider.
```

Never commit real credentials or production secrets to GitHub.

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

### 7. Create an Administrator

```bash
python manage.py createsuperuser
```

### 8. Start the Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Environment Configuration

The platform requires appropriate configuration for:

- Django secret key.
- Debug and allowed-host settings.
- PostgreSQL database connection.
- AI provider credentials.
- Embedding model configuration.
- Document storage configuration.
- Email settings, if enabled.

Refer to the repository's settings modules and `.env.example` for the exact environment variable names.

---

## Testing

Run the complete Django test suite:

```bash
python manage.py test
```

Check project configuration:

```bash
python manage.py check
```

Check migration consistency:

```bash
python manage.py makemigrations --check --dry-run
```

Testing should cover:

- Authentication and role-based permissions.
- Academic management.
- Document upload and access.
- Document publishing.
- Document engagement tracking.
- RAG document processing.
- Embedding generation and retrieval.
- Student conversational workflows.
- Teacher dashboard functionality.

---

## Security

Security is an important part of LearnMetrics AI.

The application incorporates:

- Role-based access control.
- Authenticated user access.
- Teacher and student authorization.
- Controlled document publishing.
- Protected academic resources.
- Environment-based secret management.
- Server-side validation.
- PostgreSQL relational integrity.

Production deployments should use HTTPS, secure cookie settings, restricted database credentials, private document storage and appropriate backup procedures.

---

## Contributing

Contributions and improvements are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Test your changes.
5. Submit a pull request with a clear description.

Please avoid committing credentials, environment files, database backups or private academic documents.

---

## License



---

## Author

**ChaitanyaCodec**

GitHub: [https://github.com/ChaitanyaCodec](https://github.com/ChaitanyaCodec)

Project Repository: [LearnMetrics AI](https://github.com/ChaitanyaCodec/LearnMetricsAi)

---

<p align="center">

**LearnMetrics AI**

*Making education more intelligent through AI, document intelligence and meaningful academic insights.*

</p>
