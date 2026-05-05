# 1. Project Name
**DevNest** - Collaborative Academic Learning Platform

---

# 2. Project Description
DevNest is a comprehensive academic collaboration platform designed to centralize student learning within structured course communities called "Nests". The platform combines discussion forums, organized course content, assessments, and dynamic student recognition to enhance learning outcomes and foster academic communities.

**Core Mission:** Enable instructors and students to collaborate effectively while tracking progress and recognizing contributions.

**Tech Stack:** Django 5.2.13, Python 3.x, Bootstrap 5.3.3, SQLite3/PostgreSQL

---

# 3. Objective

- Enable structured academic collaboration within course-based communities.
- Provide clear access to discussions, learning content, and assessments in one platform.
- Support instructors in managing classes, tracking progress, and grading effectively.
- Encourage student engagement through recognition, notifications, and collaborative learning.
- Improve learning outcomes by reducing repeated questions and organizing reusable knowledge.

---

# 4. Features List

## Implemented Features

### Community System (Nests)
-  Create and manage course-based communities (Nests)
-  Role-based access control (Instructor, Assistant, Student)
-  Join requests with staff approval workflow
-  Nest status management (PENDING, APPROVED, REJECTED)
-  Member status tracking (PENDING, ACTIVE, REJECTED)
-  Nest dashboard with overview of posts, content, assessments

### Discussion & Engagement System
-  Post creation with rich content support
-  Post voting system (Upvote/Downvote)
-  Comments on posts with nested discussions
-  Post tagging and categorization
-  Pinned posts for important announcements
-  Post visibility tied to active membership

### Organized Content Management
-  Hierarchical content structure (Titles → Units → Topics)
-  Multiple content types (Video, Files, Images, Text, Links)
-  Content status management (Draft/Published)
-  File upload and download tracking
-  Content sorting and organization
-  Restricted access to active members only

### Assessment System
-  Create and manage assessments (MCQ & Text questions)
-  Assessment submission tracking
-  Automatic scoring for MCQ questions
-  Manual grading interface for text answers
-  Time-limited assessments with countdown timer
-  Auto-submission on time expiry
-  Prevent duplicate submissions
-  Score and performance tracking
-  Submission result display with student feedback
-  Submissions view for instructors

### Notifications System
-  Real-time notifications for important events
-  Notification preferences (user-controlled)
-  Mark notifications as read individually or all at once
-  Notification aggregation and history

### Student Recognition & Progress
-  Dynamic student titles (14 tiers from "New Member" to "Pillar of the Nest")
-  Badge system for recognition
-  Activity-based scoring and ranking
-  User profile with contribution history
-  Recognition signals

### Moderation & Support
-  Contact Us system for user support
-  Content reporting system
-  Staff review dashboard for reported content
-  Staff management interface for messages
-  User and nest monitoring tools

### Authentication & Authorization
-  User registration and login
-  Role-based permission system
-  Session management
-  Profile management
-  Active membership enforcement across all features

---

# 5. User Stories

## Site-Staff (Platform Administrators)
- As a site staff, I can approve or reject Nest creation requests to maintain platform quality
- As a site staff, I want to manage all Nests' technical issues to ensure platform stability
- As a site staff, I want to check contact us messages and reply to them for customer support
- As a site staff, I want to check reports and be able to access where that report came from for moderation
- As a site staff, I shall be able to monitor Nests and Users when I need to for compliance
- As a site staff, I want to track overall system performance so that I can improve the platform

---

## Nest-Staff (Instructors & Assistants)

### Instructor Role
- As an instructor, I want to create and manage course content (Titles, Units, Topics) so that students can learn effectively
- As an instructor, I can approve or reject Students' requests to join Nest to control class membership
- As an instructor, I want to monitor students' progress through assessments so that I can evaluate their performance
- As an instructor, I want to create assessments with MCQ and text questions so that I can test students' understanding
- As an instructor, I want to view and grade student submissions so that I can provide feedback
- As an instructor, I want to interact with students through posts and discussions so that I can support their learning
- As an instructor, I want to be able to send announcements and students be notified to keep everyone informed

### Assistant Role
- As an assistant, I want to help answer students' questions in discussions so that I can support the instructor
- As an assistant, I want to manage discussions so that the learning environment stays organized
- As an assistant, I want to assist in content management so that the platform stays updated

---

## Nest Members (Students)
- As a Member, I want to join a Nest community so that I can access learning resources
- As a Member, I want to ask and answer questions in discussions so that I can improve my understanding
- As a Member, I want to view organized course content clearly so that I can study effectively
- As a Member, I want to take assessments and see my scores so that I can evaluate my understanding
- As a Member, I want to receive notifications so that I stay updated with new changes
- As a Member, I want to track my progress and recognition so that I can improve my performance
- As a Member, I want to see my earned titles and badges so that I feel recognized for my contributions

---

# 6. UML (Database Architecture)
![alt text](<DevNest (UML).jpeg>)
---

# 7. Wireframe & UI Layout

*To be added by contributor - Add your UI wireframes, page layouts, and design system documentation here*

---

# Installation & Setup

## Prerequisites
- Python 3.8+
- pip or conda
- Virtual environment

## Quick Start
```bash
# Clone the repository
git clone <repo-url>
cd DevNest

# Create virtual environment
python -m venv projEnv
source projEnv/bin/activate  # On Windows: projEnv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Access at http://localhost:8000
```

---

# Team & Contributors

- **Contributor 1:** [Mohammed Alqadda]
- **Contributor 2:** [Abdullah Alharbi]
- **Contributor 3:** [Mohsen Alfawaz]

---
