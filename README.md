# EDUMCP

<div align="center">
  <a href="https://aichildedu.xyz/">
    <img src="https://github.com/aieducations/edumcp/refs/heads/main/assets/logo.jpg" margin-top="15px" margin-bottom="15px" width="80%" alt="Logo">
  </a>
</div>

EDUMCP, short for Educational Model Context Protocol, is an innovative open platform protocol designed to break down the silo effect currently seen in AI applications within education. Built on the robust Model Context Protocol (MCP), EDUMCP enables seamless interconnection and interoperability among diverse AI models, educational applications, smart hardware, and even teaching content.

An AI tutoring system can easily share and understand data and context with a story generation model, an interactive game engine, or a virtual experiment platform. By establishing such a standardized communication bridge, EDUMCP brings unprecedented possibilities to the field of education, enabling various AI tools to work together to provide users with richer, more personalized, and more inspiring learning content and services.




**EDUMCP One-Sentence Video Creation Framework**

You only need to provide a one-sentence topic, and EDUMCP can generate a roughly 30-60 second animated video for children. It will support translation of English: dialogue content modification and image changes.
like：Create an video that EDUMCP robot that makes the ROYA start to enjoy learning.


[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-18%2B-blue)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110.0-blue)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-24.0.5-blue)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16.1-blue)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/mongodb-6.0-blue)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/redis-7.4-blue)](https://redis.io/)
[![Elasticsearch](https://img.shields.io/badge/elasticsearch-9.1-blue)](https://www.elastic.co/elasticsearch/)


## Overview

AICHILDEDU is an innovative educational platform designed specifically for children, leveraging the power of AI to create engaging, personalized, and educational content. The platform uses a microservice architecture to deliver a variety of AI-powered educational experiences, allowing for flexible scaling and feature expansion.

## Features

- **Personalized Story Generation**: Create custom educational stories tailored to specific age groups, themes, and educational focuses
- **Educational Quiz Creation**: Generate engaging quizzes and questions that reinforce learning objectives
- **Multimedia Integration**: Combine text, images, voice, and video into comprehensive educational materials
- **Age-Appropriate Content**: Content customization based on age groups and developmental stages
- **Multi-Language Support**: Support for content generation in multiple languages
- **User Management**: Comprehensive user system with parent, teacher, and admin roles
- **Parental Controls**: Robust parental control features to ensure child-appropriate content
- **Asynchronous Processing**: Non-blocking task execution for resource-intensive AI operations

## System Architecture

EDUMCP follows a microservice architecture with the following key components:

```
                           ┌─────────────────┐
                           │   API Gateway   │
                           └───────┬─────────┘
                                   │
┌────────┬────────┬────────────────┼────────────────┬────────────────┐
│        │        │                │                │                │
▼        ▼        ▼                ▼                ▼                ▼
┌──────────┐ ┌─────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   User   │ │ Content │ │ Learning     │ │Recommendation│ │  Analytics   │
│ Service  │ │ Service │ │ Service      │ │   Service    │ │   Service    │
└──────────┘ └─────────┘ └──────────────┘ └──────────────┘ └──────────────┘
                                 ┌──────────────────────────┐
                                 │       AI Services        │
                                 │                          │
                                 │ ┌─────────┐ ┌─────────┐  │
                                 │ │  Text   │ │ Image   │  │
                                 │ │Generator│ │Generator│  │
                                 │ └─────────┘ └─────────┘  │
                                 │ ┌─────────┐ ┌─────────┐  │
                                 │ │  Voice  │ │  Video  │  │
                                 │ │Generator│ │Generator│  │
                                 │ └─────────┘ └─────────┘  │
                                 └──────────────────────────┘
```

## Technologies Used

- **Backend**: Python, FastAPI, Uvicorn
- **Databases**: PostgreSQL, MongoDB, Redis
- **AI & ML**: LangChain, EDUMCP GPT models, TensorFlow, PyTorch, Transformers
- **Storage**: MinIO (Object Storage)
- **Search**: Elasticsearch
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT-based authentication

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10 or higher (for local development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/CHILDEDUAI/aichildedu.git
   cd aichildedu
   ```

2. Create an `.env` file in the root directory with the following variables:
   ```
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   MONGODB_URI=mongodb://mongodb:27017/
   MONGODB_DB=EDUMCP
   
   # Authentication
   SECRET_KEY=your_secret_key_change_in_production
   ```

3. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. The API Gateway will be available at `http://localhost:8000`

### Local Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the desired service:
   ```bash
   uvicorn aichildedu.user_service.main:app --reload --port 8001
   ```

## Usage Examples

### Generating a Story

```python
import requests

api_url = "http://localhost:8000/api/v1/ai/text/story"

story_request = {
    "title": "The Curious Robot",
    "theme": "Technology and Friendship",
    "age_group": "6-8",
    "characters": [
        {
            "name": "Robo",
            "description": "A curious and friendly robot who wants to learn about the world"
        },
        {
            "name": "Mia",
            "description": "A smart girl who loves technology and building things"
        }
    ],
    "educational_focus": "Introduction to robotics and programming concepts",
    "length": "medium",
    "language": "en"
}

response = requests.post(api_url, json=story_request)
task = response.json()

print(f"Story generation task created: {task['task_id']}")
print(f"Check status at: {task['status_check_url']}")
```

### Checking Task Status

```python
import requests

task_id = "task_12345"
status_url = f"http://localhost:8000/api/v1/ai/text/tasks/{task_id}"

response = requests.get(status_url)
status = response.json()

print(f"Task status: {status['status']}")
print(f"Progress: {status['progress']}%")
```

### Retrieving Generated Content

```python
import requests

task_id = "task_12345"
result_url = f"http://localhost:8000/api/v1/ai/text/tasks/{task_id}/result"

response = requests.get(result_url)
story = response.json()

print(f"Story Title: {story['title']}")
print(f"Summary: {story['summary']}")
print("\nContent:")
print(story['content'])
```

## API Documentation

The API documentation is available at:

- API Gateway: `http://localhost:8000/docs`
- User Service: `http://localhost:8001/docs`
- Content Service: `http://localhost:8002/docs`
- Learning Service: `http://localhost:8003/docs`
- AI Text Generator: `http://localhost:8010/docs`
- AI Image Generator: `http://localhost:8011/docs`
- AI Voice Generator: `http://localhost:8012/docs`
- AI Video Generator: `http://localhost:8013/docs`

## Service Architecture

### User Service

Handles user management, authentication, and authorization. Manages user profiles, child accounts, and parental controls.

### Content Service

Manages educational content creation, storage, retrieval, and organization with the following features:

- **Content Types Management**:
  - **Stories**: Interactive educational narratives with character development, themes, and moral lessons
  - **Quizzes**: Customizable question sets with answers, difficulty levels, and scoring mechanisms
  - **Lessons**: Structured learning materials with educational objectives and prerequisites

- **Content Organization**:
  - **Categories**: Hierarchical organization of content with parent-child relationships 
  - **Tags**: Flexible content labeling for improved discoverability and filtering
  - **Collections**: User-created or curated sets of content (custom, curriculum, featured)

- **Content Filtering and Search**:
  - Age-appropriate filtering based on min/max age ranges
  - Difficulty level filtering (beginner, intermediate, advanced)
  - Content rating filtering (G, PG, educational)
  - Multi-language support
  - Full-text search capabilities

- **Content Metadata**:
  - Educational value tracking
  - Subjects and themes classification
  - Reading time estimation
  - Word count metrics

- **User Interaction**:
  - Content reactions (like, favorite, helpful)
  - Content sharing and permissions
  - User-specific content collections

- **Multimedia Asset Management**:
  - Storage and retrieval of images, audio, and video assets
  - Asset association with educational content

### Learning Service

Tracks learning progress, personalized learning paths, and educational achievements with the following features:

- **Learning Path Management**:
  - **Curriculum Design**: Structured learning paths based on age groups and subjects
  - **Prerequisites**: Dependency management for learning materials
  - **Progress Tracking**: Real-time monitoring of learning milestones
  - **Adaptive Learning**: Dynamic adjustment of content difficulty based on performance

- **Assessment and Evaluation**:
  - **Progress Assessment**: Regular evaluation of learning outcomes
  - **Skill Level Analysis**: Tracking of subject-specific competencies
  - **Performance Metrics**: Detailed analytics of learning activities
  - **Achievement System**: Gamified rewards and badges for accomplishments

- **Personalization Features**:
  - **Learning Style Detection**: Identification of individual learning preferences
  - **Content Recommendations**: AI-powered suggestions for next learning steps
  - **Pace Adjustment**: Flexible learning speed based on individual progress
  - **Interest-Based Learning**: Content tailoring based on demonstrated interests

- **Progress Reporting**:
  - **Detailed Analytics**: Comprehensive learning progress visualization
  - **Parent/Teacher Dashboard**: Monitoring tools for guardians and educators
  - **Progress Reports**: Regular automated assessment summaries
  - **Learning Insights**: AI-generated recommendations for improvement

- **Collaborative Learning**:
  - **Peer Learning**: Facilitated group learning activities
  - **Social Interaction**: Safe, moderated peer communication
  - **Group Projects**: Collaborative educational tasks
  - **Shared Achievements**: Community learning milestones

- **Learning Support**:
  - **AI Tutoring**: Intelligent assistance for difficult concepts
  - **Homework Help**: Guided problem-solving support
  - **Review Sessions**: Automated review of challenging materials
  - **Learning Resources**: Additional materials for deeper understanding

### AI Services

#### Text Generator

Creates educational stories and quizzes with the following features:
- Personalized story generation based on age, theme, and educational focus
- Quiz generation with customizable difficulty levels
- Asynchronous task processing for better resource management
- Template-based content customization

#### Image Generator

Creates illustrations to accompany educational content:
- Story illustration generation
- Character visualization
- Educational diagrams and charts

#### Voice Generator

Provides audio narration for educational content:
- Story narration with different character voices
- Multi-language support
- Age-appropriate voice adaptation

#### Video Generator

Creates educational videos and animations:
- Story animations
- Educational concept visualizations
- Interactive learning content

## Development and Contribution

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Write tests for new features
5. Submit a pull request

### Code Style

This project follows PEP 8 style guidelines. Please ensure your code adheres to these standards before submitting PRs.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
