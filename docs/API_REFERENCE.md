# MCP Server API

**Version:** 0.1.0  
**Generated:** 2025-08-13 13:41:00  

Model Context Protocol server with vector database and LLM integration

## Base URL

- http://localhost:8000/api/v1

## Table of Contents

- [Admin](#admin)
- [Authentication](#authentication)
- [Documents](#documents)
- [Health](#health)
- [Other](#other)
- [Protected](#protected)
- [Resources](#resources)
- [System](#system)
- [Tools](#tools)
- [Vector Operations](#vector-operations)
- [Email Bulk](#email-bulk)
- [Email Crud](#email-crud)
- [Email Ingestion](#email-ingestion)
- [Email Stats](#email-stats)
- [Emails](#emails)
- [People](#people)
- [Project Crud](#project-crud)
- [Project People](#project-people)
- [Project Search](#project-search)
- [Project Stats](#project-stats)
- [Projects](#projects)

---

## Admin

### 🟢 **GET** /api/v1/admin/users

**List Users**

List all users (admin only)

**Operation ID:** `list_users_api_v1_admin_users_get`


**Responses:**
- `200`: Successful Response

**Authentication Required:** ✅

---

## Authentication

### 🔵 **POST** /api/v1/auth/change-password

**Change Password**

Change current user's password

**Operation ID:** `change_password_api_v1_auth_change_password_post`


**Request Body:**
- Schema: `PasswordChangeRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `MessageResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/auth/login

**Login**

Authenticate user and return access token

**Operation ID:** `login_api_v1_auth_login_post`


**Request Body:**
- Schema: `LoginRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `TokenResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

### 🔵 **POST** /api/v1/auth/logout

**Logout**

Logout user (invalidate session if using sessions)

**Operation ID:** `logout_api_v1_auth_logout_post`


**Responses:**
- `200`: Successful Response
  - Returns: `MessageResponse`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/auth/me

**Get Me**

Get current user information

**Operation ID:** `get_me_api_v1_auth_me_get`


**Responses:**
- `200`: Successful Response
  - Returns: `UserProfile`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/auth/refresh

**Refresh Token**

Refresh access token

**Operation ID:** `refresh_token_api_v1_auth_refresh_post`


**Responses:**
- `200`: Successful Response
  - Returns: `TokenResponse`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/auth/register

**Register**

Register a new user

**Operation ID:** `register_api_v1_auth_register_post`


**Request Body:**
- Schema: `RegisterRequest`
- Required: ✅


**Responses:**
- `201`: Successful Response
  - Returns: `UserResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

### 🔵 **POST** /api/v1/auth/reset-password

**Reset Password**

Request password reset

**Operation ID:** `reset_password_api_v1_auth_reset_password_post`


**Request Body:**
- Schema: `PasswordResetRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `MessageResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

## Documents

### 🟢 **GET** /api/v1/documents/

**List Documents**

List all documents (protected endpoint)

**Operation ID:** `list_documents_api_v1_documents__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `DocumentList`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/documents/

**Create Document**

Create a new document (protected endpoint)

**Operation ID:** `create_document_api_v1_documents__post`


**Request Body:**
- Schema: `DocumentCreate`
- Required: ✅


**Responses:**
- `201`: Successful Response
  - Returns: `DocumentResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/documents/**{document_id}**

**Delete Document**

Delete a document (protected endpoint)

**Operation ID:** `delete_document_api_v1_documents__document_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/documents/**{document_id}**

**Get Document**

Get a specific document (protected endpoint)

**Operation ID:** `get_document_api_v1_documents__document_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `DocumentResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Health

### 🟢 **GET** /api/v1/alive

**Alive Check**

Alternative liveness check endpoint

**Operation ID:** `alive_check_api_v1_alive_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/health

**Health Check**

Check service health status

**Operation ID:** `health_check_api_v1_health_get`


**Responses:**
- `200`: Successful Response
  - Returns: `HealthResponse`

---

### 🟢 **GET** /api/v1/health/detailed

**Health Check Detailed**

Detailed health check with component status

**Operation ID:** `health_check_detailed_api_v1_health_detailed_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/live

**Liveness Check**

Kubernetes liveness probe

**Operation ID:** `liveness_check_api_v1_live_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/metrics

**Metrics Endpoint**

Get application metrics

**Operation ID:** `metrics_endpoint_api_v1_metrics_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/ping

**Ping**

Simple ping endpoint

**Operation ID:** `ping_api_v1_ping_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/ready

**Readiness Check**

Kubernetes readiness probe

**Operation ID:** `readiness_check_api_v1_ready_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/version

**Version Info**

Get version information

**Operation ID:** `version_info_api_v1_version_get`


**Responses:**
- `200`: Successful Response

---

## Other

### 🟢 **GET** /

**Root**

Redirect to documentation

**Operation ID:** `root__get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /api/v1/info

**Api Info**

Get API information

**Operation ID:** `api_info_api_v1_info_get`


**Responses:**
- `200`: Successful Response

---

### 🟢 **GET** /metrics

**Metrics**

Prometheus metrics endpoint

**Operation ID:** `metrics_metrics_get`


**Responses:**
- `200`: Successful Response

---

## Protected

### 🟢 **GET** /api/v1/protected/resource

**Get Protected Resource**

A protected resource endpoint for testing

**Operation ID:** `get_protected_resource_api_v1_protected_resource_get`


**Responses:**
- `200`: Successful Response

**Authentication Required:** ✅

---

## Resources

### 🟢 **GET** /api/v1/resources

**List Resources**

List all available resources

**Operation ID:** `list_resources_api_v1_resources_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `authorization` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `ResourceListResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

### 🟢 **GET** /api/v1/resources/**{resource_uri}**

**Read Resource**

Read a specific resource

**Operation ID:** `read_resource_api_v1_resources__resource_uri__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `resource_uri` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `ResourceReadResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## System

### 🟢 **GET** /api/v1/system/cache/stats

**Cache Stats**

Get cache statistics - requires authentication

**Operation ID:** `cache_stats_api_v1_system_cache_stats_get`


**Responses:**
- `200`: Successful Response

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/system/database/stats

**Database Stats**

Get database statistics - requires authentication

**Operation ID:** `database_stats_api_v1_system_database_stats_get`


**Responses:**
- `200`: Successful Response

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/system/info

**System Info**

Get system information - requires authentication

**Operation ID:** `system_info_api_v1_system_info_get`


**Responses:**
- `200`: Successful Response

**Authentication Required:** ✅

---

## Tools

### 🟢 **GET** /api/v1/tools

**List Tools**

List all available tools

**Operation ID:** `list_tools_api_v1_tools_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `authorization` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `ToolListResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

### 🔵 **POST** /api/v1/tools/**{tool_name}**/execute

**Execute Tool**

Execute a specific tool

**Operation ID:** `execute_tool_api_v1_tools__tool_name__execute_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | ✅ | - |


**Request Body:**
- Schema: `ToolExecutionRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `ToolExecutionResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Vector Operations

### 🔴 **DELETE** /api/v1/vectors/documents/**{document_id}**

**Delete Document**

Delete a document from vector database

**Operation ID:** `delete_document_api_v1_vectors_documents__document_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/vectors/embed

**Generate Embeddings**

Generate embeddings for text

**Operation ID:** `generate_embeddings_api_v1_vectors_embed_post`


**Request Body:**
- Schema: `EmbeddingRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmbeddingResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/vectors/ingest

**Ingest Documents**

Ingest documents into vector database

**Operation ID:** `ingest_documents_api_v1_vectors_ingest_post`


**Request Body:**
- Schema: `DocumentIngestionRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `DocumentIngestionResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/vectors/search

**Search Vectors**

Search for similar documents

**Operation ID:** `search_vectors_api_v1_vectors_search_post`


**Request Body:**
- Schema: `VectorSearchRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `VectorSearchResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/vectors/stats

**Get Vector Stats**

Get vector database statistics

**Operation ID:** `get_vector_stats_api_v1_vectors_stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `authorization` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

---

## Email Bulk

### 🔵 **POST** /api/v1/emails/bulk-update

**Bulk Update Emails**

Bulk update multiple emails

**Operation ID:** `bulk_update_emails_api_v1_emails_bulk_update_post`


**Request Body:**
- Schema: `BulkEmailUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/assign-project

**Bulk Assign Emails To Project**

Bulk assign emails to a project

**Operation ID:** `bulk_assign_emails_to_project_api_v1_emails_bulk_assign_project_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/delete

**Bulk Delete Emails**

Bulk delete emails

**Operation ID:** `bulk_delete_emails_api_v1_emails_bulk_delete_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/mark-read

**Bulk Mark Emails Read**

Bulk mark emails as read

**Operation ID:** `bulk_mark_emails_read_api_v1_emails_bulk_mark_read_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Email Crud

### 🟢 **GET** /api/v1/emails/

**List Emails**

List emails with pagination

**Operation ID:** `list_emails_api_v1_emails__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |
| `project_id` | string | ❌ | - |
| `is_read` | string | ❌ | - |
| `is_flagged` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/by-message-id/**{message_id}**

**Get Email By Message Id**

Get email by external message ID

**Operation ID:** `get_email_by_message_id_api_v1_emails_by_message_id__message_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/search

**Search Emails Advanced**

Search emails with various filters

**Operation ID:** `search_emails_advanced_api_v1_emails_search_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ❌ | Search query for subject/body |
| `from` | string | ❌ | Filter by sender email |
| `to` | string | ❌ | Filter by recipient email |
| `start_date` | string | ❌ | Start date for date range |
| `end_date` | string | ❌ | End date for date range |
| `project_id` | string | ❌ | Filter by project ID |
| `thread_id` | string | ❌ | Filter by thread ID |
| `is_read` | string | ❌ | Filter by read status |
| `is_flagged` | string | ❌ | Filter by flagged status |
| `page` | integer | ❌ | Page number |
| `size` | integer | ❌ | Items per page |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/thread/**{thread_id}**

**Get Thread Emails**

Get all emails in a thread

**Operation ID:** `get_thread_emails_api_v1_emails_thread__thread_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/emails/**{email_id}**

**Delete Email**

Delete an email

**Operation ID:** `delete_email_api_v1_emails__email_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/**{email_id}**

**Get Email**

Get email by ID

**Operation ID:** `get_email_api_v1_emails__email_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟠 **PATCH** /api/v1/emails/**{email_id}**

**Update Email**

Update email properties

**Operation ID:** `update_email_api_v1_emails__email_id__patch`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Request Body:**
- Schema: `EmailUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/assign-project

**Assign Email To Project**

Assign an email to a project

**Operation ID:** `assign_email_to_project_api_v1_emails__email_id__assign_project_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/flag

**Flag Email**

Flag an email

**Operation ID:** `flag_email_api_v1_emails__email_id__flag_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/mark-read

**Mark Email As Read**

Mark an email as read

**Operation ID:** `mark_email_as_read_api_v1_emails__email_id__mark_read_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/mark-unread

**Mark Email As Unread**

Mark an email as unread

**Operation ID:** `mark_email_as_unread_api_v1_emails__email_id__mark_unread_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/unflag

**Unflag Email**

Unflag an email

**Operation ID:** `unflag_email_api_v1_emails__email_id__unflag_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Email Ingestion

### 🔵 **POST** /api/v1/emails/ingest

**Ingest Email**

Ingest a new email into the system

**Operation ID:** `ingest_email_api_v1_emails_ingest_post`


**Request Body:**
- Schema: `EmailIngest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/ingest/bulk

**Ingest Bulk Emails**

Bulk ingest multiple emails

**Operation ID:** `ingest_bulk_emails_api_v1_emails_ingest_bulk_post`


**Request Body:**
- Required: ✅


**Responses:**
- `201`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Email Stats

### 🟢 **GET** /api/v1/emails/statistics/overview

**Get Email Statistics Legacy**

Get email statistics (legacy endpoint for backward compatibility)

**Operation ID:** `get_email_statistics_legacy_api_v1_emails_statistics_overview_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | ❌ | - |
| `date_to` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailStatistics`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats

**Get Email Statistics**

Get overall email statistics

**Operation ID:** `get_email_statistics_api_v1_emails_stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | ❌ | - |
| `date_to` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats/project/**{project_id}**

**Get Project Email Statistics**

Get email statistics for a specific project

**Operation ID:** `get_project_email_statistics_api_v1_emails_stats_project__project_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats/timeline

**Get Email Activity Timeline**

Get email activity timeline

**Operation ID:** `get_email_activity_timeline_api_v1_emails_stats_timeline_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | ❌ | Number of days to include |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Emails

### 🟢 **GET** /api/v1/emails/

**List Emails**

List emails with pagination

**Operation ID:** `list_emails_api_v1_emails__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |
| `project_id` | string | ❌ | - |
| `is_read` | string | ❌ | - |
| `is_flagged` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk-update

**Bulk Update Emails**

Bulk update multiple emails

**Operation ID:** `bulk_update_emails_api_v1_emails_bulk_update_post`


**Request Body:**
- Schema: `BulkEmailUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/assign-project

**Bulk Assign Emails To Project**

Bulk assign emails to a project

**Operation ID:** `bulk_assign_emails_to_project_api_v1_emails_bulk_assign_project_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/delete

**Bulk Delete Emails**

Bulk delete emails

**Operation ID:** `bulk_delete_emails_api_v1_emails_bulk_delete_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/bulk/mark-read

**Bulk Mark Emails Read**

Bulk mark emails as read

**Operation ID:** `bulk_mark_emails_read_api_v1_emails_bulk_mark_read_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/by-message-id/**{message_id}**

**Get Email By Message Id**

Get email by external message ID

**Operation ID:** `get_email_by_message_id_api_v1_emails_by_message_id__message_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/ingest

**Ingest Email**

Ingest a new email into the system

**Operation ID:** `ingest_email_api_v1_emails_ingest_post`


**Request Body:**
- Schema: `EmailIngest`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/ingest/bulk

**Ingest Bulk Emails**

Bulk ingest multiple emails

**Operation ID:** `ingest_bulk_emails_api_v1_emails_ingest_bulk_post`


**Request Body:**
- Required: ✅


**Responses:**
- `201`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/search

**Search Emails Advanced**

Search emails with various filters

**Operation ID:** `search_emails_advanced_api_v1_emails_search_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ❌ | Search query for subject/body |
| `from` | string | ❌ | Filter by sender email |
| `to` | string | ❌ | Filter by recipient email |
| `start_date` | string | ❌ | Start date for date range |
| `end_date` | string | ❌ | End date for date range |
| `project_id` | string | ❌ | Filter by project ID |
| `thread_id` | string | ❌ | Filter by thread ID |
| `is_read` | string | ❌ | Filter by read status |
| `is_flagged` | string | ❌ | Filter by flagged status |
| `page` | integer | ❌ | Page number |
| `size` | integer | ❌ | Items per page |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/statistics/overview

**Get Email Statistics Legacy**

Get email statistics (legacy endpoint for backward compatibility)

**Operation ID:** `get_email_statistics_legacy_api_v1_emails_statistics_overview_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | ❌ | - |
| `date_to` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailStatistics`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats

**Get Email Statistics**

Get overall email statistics

**Operation ID:** `get_email_statistics_api_v1_emails_stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | ❌ | - |
| `date_to` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats/project/**{project_id}**

**Get Project Email Statistics**

Get email statistics for a specific project

**Operation ID:** `get_project_email_statistics_api_v1_emails_stats_project__project_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/stats/timeline

**Get Email Activity Timeline**

Get email activity timeline

**Operation ID:** `get_email_activity_timeline_api_v1_emails_stats_timeline_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | ❌ | Number of days to include |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/thread/**{thread_id}**

**Get Thread Emails**

Get all emails in a thread

**Operation ID:** `get_thread_emails_api_v1_emails_thread__thread_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/emails/**{email_id}**

**Delete Email**

Delete an email

**Operation ID:** `delete_email_api_v1_emails__email_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/emails/**{email_id}**

**Get Email**

Get email by ID

**Operation ID:** `get_email_api_v1_emails__email_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟠 **PATCH** /api/v1/emails/**{email_id}**

**Update Email**

Update email properties

**Operation ID:** `update_email_api_v1_emails__email_id__patch`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Request Body:**
- Schema: `EmailUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/assign-project

**Assign Email To Project**

Assign an email to a project

**Operation ID:** `assign_email_to_project_api_v1_emails__email_id__assign_project_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/flag

**Flag Email**

Flag an email

**Operation ID:** `flag_email_api_v1_emails__email_id__flag_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/mark-read

**Mark Email As Read**

Mark an email as read

**Operation ID:** `mark_email_as_read_api_v1_emails__email_id__mark_read_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/mark-unread

**Mark Email As Unread**

Mark an email as unread

**Operation ID:** `mark_email_as_unread_api_v1_emails__email_id__mark_unread_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/emails/**{email_id}**/unflag

**Unflag Email**

Unflag an email

**Operation ID:** `unflag_email_api_v1_emails__email_id__unflag_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `EmailResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## People

### 🟢 **GET** /api/v1/people/

**List People**

List all people with pagination

**Operation ID:** `list_people_api_v1_people__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |
| `is_active` | string | ❌ | - |
| `is_external` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/people/

**Create Person**

Create a new person

**Operation ID:** `create_person_api_v1_people__post`


**Request Body:**
- Schema: `PersonCreate`
- Required: ✅


**Responses:**
- `201`: Successful Response
  - Returns: `PersonResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/autocomplete

**Autocomplete People**

Autocomplete people for UI

**Operation ID:** `autocomplete_people_api_v1_people_autocomplete_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prefix` | string | ✅ | Name or email prefix |
| `limit` | integer | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/by-email/**{email}**

**Get Person By Email**

Get person by email address

**Operation ID:** `get_person_by_email_api_v1_people_by_email__email__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `email` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `PersonResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/search

**Search People**

Search people with various filters

**Operation ID:** `search_people_api_v1_people_search_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ❌ | Search query |
| `organization` | string | ❌ | - |
| `domain` | string | ❌ | - |
| `is_active` | string | ❌ | - |
| `is_external` | string | ❌ | - |
| `limit` | integer | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/people/**{person_id}**

**Delete Person**

Delete a person

**Operation ID:** `delete_person_api_v1_people__person_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/**{person_id}**

**Get Person**

Get person by ID

**Operation ID:** `get_person_api_v1_people__person_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `PersonResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟠 **PATCH** /api/v1/people/**{person_id}**

**Update Person**

Update person information (partial update)

**Operation ID:** `update_person_api_v1_people__person_id__patch`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Request Body:**
- Schema: `PersonUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `PersonResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟡 **PUT** /api/v1/people/**{person_id}**

**Replace Person**

Replace person information (full update)

**Operation ID:** `replace_person_api_v1_people__person_id__put`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Request Body:**
- Schema: `PersonUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `PersonResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/**{person_id}**/emails

**Get Person Emails**

Get emails sent and received by a person

**Operation ID:** `get_person_emails_api_v1_people__person_id__emails_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/people/**{person_id}**/merge

**Merge People**

Merge two person records

**Operation ID:** `merge_people_api_v1_people__person_id__merge_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Request Body:**
- Schema: `MergeRequest`
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/**{person_id}**/projects

**Get Person Projects**

Get projects associated with a person

**Operation ID:** `get_person_projects_api_v1_people__person_id__projects_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/people/**{person_id}**/projects/**{project_id}**

**Remove Person From Project**

Remove person from project

**Operation ID:** `remove_person_from_project_api_v1_people__person_id__projects__project_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/people/**{person_id}**/projects/**{project_id}**

**Add Person To Project**

Add person to project

**Operation ID:** `add_person_to_project_api_v1_people__person_id__projects__project_id__post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |
| `project_id` | string | ✅ | - |


**Request Body:**
- Schema: `Body_add_person_to_project_api_v1_people__person_id__projects__project_id__post`


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/people/**{person_id}**/stats

**Get Person Statistics**

Get statistics for a person

**Operation ID:** `get_person_statistics_api_v1_people__person_id__stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `person_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `PersonStatistics`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Project Crud

### 🟢 **GET** /api/v1/projects/

**List Projects**

List projects with pagination

**Operation ID:** `list_projects_api_v1_projects__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |
| `is_active` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/

**Create Project**

Create a new project

**Operation ID:** `create_project_api_v1_projects__post`


**Request Body:**
- Schema: `ProjectCreate`
- Required: ✅


**Responses:**
- `201`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/projects/**{project_id}**

**Delete Project**

Delete a project

**Operation ID:** `delete_project_api_v1_projects__project_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**

**Get Project**

Get project by ID

**Operation ID:** `get_project_api_v1_projects__project_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟠 **PATCH** /api/v1/projects/**{project_id}**

**Update Project**

Update project information

**Operation ID:** `update_project_api_v1_projects__project_id__patch`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Schema: `ProjectUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟡 **PUT** /api/v1/projects/**{project_id}**

**Replace Project**

Replace/fully update a project

**Operation ID:** `replace_project_api_v1_projects__project_id__put`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Schema: `ProjectUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Project People

### 🔵 **POST** /api/v1/projects/bulk-assign-people

**Bulk Assign People**

Bulk assign people to a project

**Operation ID:** `bulk_assign_people_api_v1_projects_bulk_assign_people_post`


**Request Body:**
- Schema: `BulkPersonProjectAssign`
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**/people

**List Project People**

List all people in a project

**Operation ID:** `list_project_people_api_v1_projects__project_id__people_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/**{project_id}**/people

**Add Person To Project**

Add a person to a project

**Operation ID:** `add_person_to_project_api_v1_projects__project_id__people_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Required: ✅


**Responses:**
- `201`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/projects/**{project_id}**/people/**{person_id}**

**Remove Person From Project**

Remove a person from a project

**Operation ID:** `remove_person_from_project_api_v1_projects__project_id__people__person_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |
| `person_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Project Search

### 🔵 **POST** /api/v1/projects/find-for-email

**Find Project For Email**

Find the appropriate project for an email address

**Operation ID:** `find_project_for_email_api_v1_projects_find_for_email_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/search

**Search Projects**

Search projects by name or domain

**Operation ID:** `search_projects_api_v1_projects_search_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ❌ | Search query |
| `domain` | string | ❌ | Email domain filter |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/test

**Test Endpoint**

Test endpoint to verify routing works - no auth required

**Operation ID:** `test_endpoint_api_v1_projects_test_get`


**Responses:**
- `200`: Successful Response

---

## Project Stats

### 🟢 **GET** /api/v1/projects/statistics/overview

**Get Project Statistics**

Get project statistics

**Operation ID:** `get_project_statistics_api_v1_projects_statistics_overview_get`


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectStatistics`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**/stats

**Get Project Stats**

Get statistics for a specific project

**Operation ID:** `get_project_stats_api_v1_projects__project_id__stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Projects

### 🟢 **GET** /api/v1/projects/

**List Projects**

List projects with pagination

**Operation ID:** `list_projects_api_v1_projects__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | ❌ | - |
| `size` | integer | ❌ | - |
| `is_active` | string | ❌ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/

**Create Project**

Create a new project

**Operation ID:** `create_project_api_v1_projects__post`


**Request Body:**
- Schema: `ProjectCreate`
- Required: ✅


**Responses:**
- `201`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/bulk-assign-people

**Bulk Assign People**

Bulk assign people to a project

**Operation ID:** `bulk_assign_people_api_v1_projects_bulk_assign_people_post`


**Request Body:**
- Schema: `BulkPersonProjectAssign`
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/find-for-email

**Find Project For Email**

Find the appropriate project for an email address

**Operation ID:** `find_project_for_email_api_v1_projects_find_for_email_post`


**Request Body:**
- Required: ✅


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/search

**Search Projects**

Search projects by name or domain

**Operation ID:** `search_projects_api_v1_projects_search_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | ❌ | Search query |
| `domain` | string | ❌ | Email domain filter |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/statistics/overview

**Get Project Statistics**

Get project statistics

**Operation ID:** `get_project_statistics_api_v1_projects_statistics_overview_get`


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectStatistics`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/test

**Test Endpoint**

Test endpoint to verify routing works - no auth required

**Operation ID:** `test_endpoint_api_v1_projects_test_get`


**Responses:**
- `200`: Successful Response

---

### 🔴 **DELETE** /api/v1/projects/**{project_id}**

**Delete Project**

Delete a project

**Operation ID:** `delete_project_api_v1_projects__project_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**

**Get Project**

Get project by ID

**Operation ID:** `get_project_api_v1_projects__project_id__get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟠 **PATCH** /api/v1/projects/**{project_id}**

**Update Project**

Update project information

**Operation ID:** `update_project_api_v1_projects__project_id__patch`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Schema: `ProjectUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟡 **PUT** /api/v1/projects/**{project_id}**

**Replace Project**

Replace/fully update a project

**Operation ID:** `replace_project_api_v1_projects__project_id__put`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Schema: `ProjectUpdate`
- Required: ✅


**Responses:**
- `200`: Successful Response
  - Returns: `ProjectResponse`
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**/people

**List Project People**

List all people in a project

**Operation ID:** `list_project_people_api_v1_projects__project_id__people_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔵 **POST** /api/v1/projects/**{project_id}**/people

**Add Person To Project**

Add a person to a project

**Operation ID:** `add_person_to_project_api_v1_projects__project_id__people_post`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Request Body:**
- Required: ✅


**Responses:**
- `201`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🔴 **DELETE** /api/v1/projects/**{project_id}**/people/**{person_id}**

**Remove Person From Project**

Remove a person from a project

**Operation ID:** `remove_person_from_project_api_v1_projects__project_id__people__person_id__delete`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |
| `person_id` | string | ✅ | - |


**Responses:**
- `204`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

### 🟢 **GET** /api/v1/projects/**{project_id}**/stats

**Get Project Stats**

Get statistics for a specific project

**Operation ID:** `get_project_stats_api_v1_projects__project_id__stats_get`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | string | ✅ | - |


**Responses:**
- `200`: Successful Response
- `422`: Validation Error
  - Returns: `HTTPValidationError`

**Authentication Required:** ✅

---

## Schemas

The following data models are used by the API:

### Body_add_person_to_project_api_v1_people__person_id__projects__project_id__post

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `person_id_param` | any | ❌ | - |
| `role` | string | ❌ | - |

### BulkEmailUpdate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email_ids` | array | ✅ | - |
| `update` | any | ✅ | - |

### BulkPersonProjectAssign

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `person_ids` | array | ✅ | - |
| `project_id` | string | ✅ | - |
| `role` | string | ❌ | - |

### DocumentCreate

Document creation schema

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `title` | string | ✅ | - |
| `content` | string | ✅ | - |
| `tags` | array | ❌ | - |

### DocumentIngestionRequest

Request to ingest documents

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `documents` | array | ✅ | - |
| `metadatas` | any | ❌ | - |
| `ids` | any | ❌ | - |

### DocumentIngestionResponse

Document ingestion result

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `document_ids` | array | ✅ | - |
| `count` | integer | ✅ | - |
| `processing_time` | number | ✅ | - |

### DocumentList

Document list response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `items` | array | ✅ | - |
| `total` | integer | ✅ | - |
| `page` | integer | ✅ | - |
| `size` | integer | ✅ | - |

### DocumentResponse

Document response schema

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `title` | string | ✅ | - |
| `content` | string | ✅ | - |
| `tags` | array | ❌ | - |
| `owner_id` | string | ✅ | - |
| `created_at` | string (date-time) | ✅ | - |
| `updated_at` | string (date-time) | ✅ | - |

### EmailIngest

Simplified email ingestion schema

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `to` | array | ✅ | - |
| `from` | string (email) | ✅ | - |
| `subject` | string | ✅ | - |
| `datetime` | string (date-time) | ✅ | - |
| `body` | string | ✅ | - |
| `cc` | array | ❌ | - |
| `body_text` | any | ❌ | - |
| `email_id` | string | ✅ | - |
| `message_id` | any | ❌ | - |
| `in_reply_to` | any | ❌ | - |
| `thread_id` | any | ❌ | - |
| `headers` | any | ❌ | - |
| `attachments` | any | ❌ | - |
| `size_bytes` | any | ❌ | - |

### EmailRecipientResponse

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `person` | any | ✅ | - |
| `recipient_type` | any | ✅ | - |

### EmailResponse

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email_id` | string | ✅ | - |
| `message_id` | any | ❌ | - |
| `in_reply_to` | any | ❌ | - |
| `thread_id` | any | ❌ | - |
| `subject` | string | ✅ | - |
| `body` | string | ✅ | - |
| `body_text` | any | ❌ | - |
| `datetime_sent` | string (date-time) | ✅ | - |
| `headers` | any | ❌ | - |
| `attachments` | any | ❌ | - |
| `size_bytes` | any | ❌ | - |
| `id` | string | ✅ | - |
| `is_read` | boolean | ✅ | - |
| `is_flagged` | boolean | ✅ | - |
| `is_draft` | boolean | ✅ | - |
| `from_person_id` | string | ✅ | - |
| `project_id` | any | ❌ | - |
| `created_at` | string (date-time) | ✅ | - |
| `updated_at` | string (date-time) | ✅ | - |
| `sender` | any | ✅ | - |
| `project` | any | ❌ | - |
| `recipients` | array | ❌ | - |
| `project_name` | any | ❌ | - |
| `has_attachments` | boolean | ❌ | - |
| `attachment_count` | integer | ❌ | - |
| `from` | any | ❌ | - |

### EmailStatistics

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `total_emails` | integer | ✅ | - |
| `unread_count` | integer | ✅ | - |
| `flagged_count` | integer | ✅ | - |
| `draft_count` | integer | ✅ | - |
| `emails_by_project` | object | ✅ | - |
| `emails_by_sender` | array | ✅ | - |
| `emails_by_date` | array | ✅ | - |
| `average_response_time` | any | ❌ | - |

### EmailSummary

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `email_id` | string | ✅ | - |
| `subject` | string | ✅ | - |
| `datetime_sent` | string (date-time) | ✅ | - |
| `sender` | any | ✅ | - |
| `is_read` | boolean | ✅ | - |
| `is_flagged` | boolean | ✅ | - |
| `thread_id` | any | ❌ | - |

### EmailUpdate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `is_read` | any | ❌ | - |
| `is_flagged` | any | ❌ | - |
| `is_draft` | any | ❌ | - |
| `project_id` | any | ❌ | - |

### EmbeddingRequest

Request to generate embeddings

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `texts` | any | ✅ | - |
| `model` | any | ❌ | - |
| `normalize` | boolean | ❌ | - |

### EmbeddingResponse

Embedding generation result

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `embeddings` | array | ✅ | - |
| `model` | string | ✅ | - |
| `dimension` | integer | ✅ | - |
| `count` | integer | ✅ | - |

### HTTPValidationError

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `detail` | array | ❌ | - |

### HealthResponse

Health check response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | string | ✅ | - |
| `version` | string | ✅ | - |
| `timestamp` | string (date-time) | ✅ | - |
| `services` | object | ✅ | - |
| `metrics` | any | ❌ | - |

### LoginRequest

Login request schema

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `username` | string | ✅ | - |
| `password` | string | ✅ | - |

### MergeRequest

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `merge_with_id` | string | ✅ | - |

### MessageResponse

Simple message response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `message` | string | ✅ | - |

### PasswordChangeRequest

Password change request

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `current_password` | string | ✅ | - |
| `new_password` | string | ✅ | - |

### PasswordResetRequest

Password reset request

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | string (email) | ✅ | - |

### PersonCreate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | string (email) | ✅ | - |
| `first_name` | any | ❌ | - |
| `last_name` | any | ❌ | - |
| `display_name` | any | ❌ | - |
| `organization` | any | ❌ | - |
| `phone` | any | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `is_external` | boolean | ❌ | - |
| `person_metadata` | any | ❌ | - |

### PersonResponse

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | string (email) | ✅ | - |
| `first_name` | any | ❌ | - |
| `last_name` | any | ❌ | - |
| `display_name` | any | ❌ | - |
| `organization` | any | ❌ | - |
| `phone` | any | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `is_external` | boolean | ❌ | - |
| `person_metadata` | any | ❌ | - |
| `id` | string | ✅ | - |
| `full_name` | string | ✅ | - |
| `created_at` | string (date-time) | ✅ | - |
| `updated_at` | string (date-time) | ✅ | - |

### PersonStatistics

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `emails_sent` | integer | ✅ | - |
| `emails_received` | integer | ✅ | - |
| `projects_count` | integer | ✅ | - |
| `first_email_date` | any | ❌ | - |
| `last_email_date` | any | ❌ | - |

### PersonSummary

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `email` | string (email) | ✅ | - |
| `full_name` | string | ✅ | - |
| `display_name` | any | ❌ | - |
| `first_name` | any | ❌ | - |
| `last_name` | any | ❌ | - |
| `organization` | any | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `is_external` | boolean | ❌ | - |

### PersonUpdate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `first_name` | any | ❌ | - |
| `last_name` | any | ❌ | - |
| `display_name` | any | ❌ | - |
| `organization` | any | ❌ | - |
| `phone` | any | ❌ | - |
| `is_active` | any | ❌ | - |
| `is_external` | any | ❌ | - |
| `person_metadata` | any | ❌ | - |

### ProjectCreate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✅ | - |
| `description` | any | ❌ | - |
| `email_domains` | array | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `auto_assign` | boolean | ❌ | - |
| `project_metadata` | any | ❌ | - |
| `tags` | array | ❌ | - |

### ProjectResponse

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✅ | - |
| `description` | any | ❌ | - |
| `email_domains` | array | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `auto_assign` | boolean | ❌ | - |
| `project_metadata` | any | ❌ | - |
| `tags` | array | ❌ | - |
| `id` | string | ✅ | - |
| `created_at` | string (date-time) | ✅ | - |
| `updated_at` | string (date-time) | ✅ | - |
| `people` | array | ❌ | - |
| `email_count` | integer | ❌ | - |

### ProjectStatistics

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `total_projects` | integer | ✅ | - |
| `active_projects` | integer | ✅ | - |
| `total_people` | integer | ✅ | - |
| `emails_per_project` | array | ✅ | - |
| `most_active_domains` | array | ✅ | - |

### ProjectSummary

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `name` | string | ✅ | - |
| `email_domains` | array | ❌ | - |

### ProjectUpdate

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | any | ❌ | - |
| `description` | any | ❌ | - |
| `email_domains` | any | ❌ | - |
| `is_active` | any | ❌ | - |
| `auto_assign` | any | ❌ | - |
| `project_metadata` | any | ❌ | - |
| `tags` | any | ❌ | - |

### RecipientTypeSchema

### RegisterRequest

User registration request

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `username` | string | ✅ | - |
| `email` | string (email) | ✅ | - |
| `password` | string | ✅ | - |
| `full_name` | any | ❌ | - |

### ResourceInfo

Resource information

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `uri` | string | ✅ | - |
| `name` | string | ✅ | - |
| `description` | string | ✅ | - |
| `mime_type` | string | ✅ | - |

### ResourceListResponse

List of available resources

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `resources` | array | ✅ | - |
| `count` | integer | ✅ | - |

### ResourceReadResponse

Resource content response

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `uri` | string | ✅ | - |
| `content` | string | ✅ | - |
| `mime_type` | string | ✅ | - |

### SearchResult

Individual search result

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `document` | string | ✅ | - |
| `score` | number | ✅ | - |
| `metadata` | any | ❌ | - |

### StatusEnum

API response status

### TokenResponse

Token response schema

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `access_token` | string | ✅ | - |
| `token_type` | string | ❌ | - |
| `expires_in` | integer | ✅ | Token expiration in seconds |

### ToolExecutionRequest

Request to execute a tool

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `arguments` | object | ❌ | - |
| `timeout` | any | ❌ | - |

### ToolExecutionResponse

Tool execution result

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `result` | any | ✅ | - |
| `execution_time` | number | ✅ | - |
| `tool_name` | string | ✅ | - |

### ToolInfo

Tool information

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `name` | string | ✅ | - |
| `description` | string | ✅ | - |
| `input_schema` | object | ✅ | - |

### ToolListResponse

List of available tools

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `tools` | array | ✅ | - |
| `count` | integer | ✅ | - |

### UserProfile

Current user profile

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `username` | string | ✅ | - |
| `email` | string (email) | ✅ | - |
| `full_name` | any | ❌ | - |
| `roles` | array | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `is_superuser` | boolean | ❌ | - |

### UserResponse

User response schema (without sensitive data)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | string | ✅ | - |
| `username` | string | ✅ | - |
| `email` | string (email) | ✅ | - |
| `full_name` | any | ❌ | - |
| `is_active` | boolean | ❌ | - |
| `is_superuser` | boolean | ❌ | - |
| `roles` | array | ❌ | - |
| `created_at` | string (date-time) | ✅ | - |
| `updated_at` | string (date-time) | ✅ | - |

### ValidationError

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `loc` | array | ✅ | - |
| `msg` | string | ✅ | - |
| `type` | string | ✅ | - |

### VectorSearchRequest

Vector search request

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `query` | string | ✅ | - |
| `limit` | integer | ❌ | - |
| `filter` | any | ❌ | - |
| `include_metadata` | boolean | ❌ | - |

### VectorSearchResponse

Vector search results

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `status` | any | ❌ | - |
| `message` | any | ❌ | - |
| `timestamp` | string (date-time) | ❌ | - |
| `results` | array | ✅ | - |
| `query` | string | ✅ | - |
| `count` | integer | ✅ | - |
| `search_time` | number | ✅ | - |

