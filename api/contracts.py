# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: API CONTRACT
# FILE: api/contracts.py
# ==============================================================================
## AUTHOR:#     Yevhenii Bondariev
## ARCHITECT:#     OpenAI GPT-5.5
## ------------------------------------------------------------------------------
#
# PURPOSE
# Единый контракт платформы.
# Данный файл является "Конституцией" REST API.
# Здесь НЕ должно быть:
#
#   • FastAPI endpoint'ов
#   • SQLAlchemy
#   • бизнес логики
#   • работы с файлами
#
# Только:
#
#   • версии API
#   • имена Swagger Tag
#   • Prefix
#   • OpenAPI metadata
#   • Error Codes
#   • Константы платформы
#
# ------------------------------------------------------------------------------
# Любой Router обязан использовать данный файл.
# ==============================================================================

# ==============================================================================
# PLATFORM
# ==============================================================================

PLATFORM_NAME = "OMNIFACTORY"

PLATFORM_DESCRIPTION = (
    "Enterprise AI Development Platform"
)

API_VERSION = "v1"
CURRENT_VERSION = "2.0.0"
API_PREFIX = f"/api/{API_VERSION}"

# ==============================================================================
# OPENAPI
# ==============================================================================

OPENAPI_TITLE = "OMNIFACTORY Enterprise API"

OPENAPI_DESCRIPTION = """
# OMNIFACTORY PLATFORM

Enterprise AI Platform.
---
## Modules

• AI
• Builder
• Registry
• Runtime
• CRM
• Deployment
• Marketplace
• Human Workspace
• Monitoring
---

OpenAPI Contract
Version 2.0
"""

OPENAPI_CONTACT = {
    "name": "OmniFactory",
    "email": "support@omnifactory.ai"
}

OPENAPI_LICENSE = {
    "name": "Enterprise"
}
# ==============================================================================
# SWAGGER TAGS
# ==============================================================================

TAG_SYSTEM = "⚡ System"
TAG_REGISTRY = "🧠 Registry"
TAG_BUILDER = "🏗 Builder"
TAG_RUNTIME = "🚀 Runtime"
TAG_DEPLOYMENT = "🚀 Deployment"
TAG_MONITORING = "📊 Monitoring"
TAG_AI = "🤖 Artificial Intelligence"
TAG_CRM = "👥 CRM"
TAG_WORKSPACE = "💼 Workspace"
TAG_MARKETPLACE = "🛒 Marketplace"
TAG_ADMIN = "🛠 Administration"
TAG_HUMAN = "🧬 Human Twin"
TAG_REPORTS = "📄 Reports"
TAG_AUTH = "🔐 Authentication"
TAG_FILES = "📁 Files"
TAG_WEBHOOK = "📡 Webhooks"

# ==============================================================================
# ROUTE PREFIXES
# ==============================================================================

SYSTEM_PREFIX = "/system"
REGISTRY_PREFIX = "/registry"
BUILDER_PREFIX = "/builder"
DEPLOYMENT_PREFIX = "/deployment"
MONITORING_PREFIX = "/monitoring"
CRM_PREFIX = "/crm"
AI_PREFIX = "/ai"
WORKSPACE_PREFIX = "/workspace"
MARKETPLACE_PREFIX = "/marketplace"
REPORT_PREFIX = "/reports"
AUTH_PREFIX = "/auth"
FILES_PREFIX = "/files"

# ==============================================================================
# STATUS
# ==============================================================================

STATUS_OK = "OK"
STATUS_RUNNING = "RUNNING"
STATUS_STOPPED = "STOPPED"
STATUS_FAILED = "FAILED"
STATUS_WARNING = "WARNING"
STATUS_PENDING = "PENDING"
STATUS_BUILDING = "BUILDING"
STATUS_DEPLOYING = "DEPLOYING"

# ==============================================================================
# DEPLOYMENT
# ==============================================================================

TARGET_TELEGRAM = "telegram"
TARGET_DISCORD = "discord"
TARGET_WEB = "web"
TARGET_DESKTOP = "desktop"
TARGET_ANDROID = "android"
TARGET_IOS = "ios"
TARGET_DOCKER = "docker"
TARGET_FASTAPI = "fastapi"

# ==============================================================================
# RUNTIME
# ==============================================================================

RUNTIME_PYTHON = "python"
RUNTIME_NODE = "node"
RUNTIME_DOTNET = "dotnet"
RUNTIME_JAVA = "java"

# ==============================================================================
# AI
# ==============================================================================

MODEL_CODELLAMA = "codellama"
MODEL_LLAMA3 = "llama3"
MODEL_GPT = "gpt"
MODEL_CLAUDE = "claude"
MODEL_GEMINI = "gemini"

# ==============================================================================
# ERROR CODES
# ==============================================================================

ERROR_OK = 0
ERROR_UNKNOWN = 1
ERROR_DATABASE = 100
ERROR_REGISTRY = 101
ERROR_BUILDER = 102
ERROR_COMPILER = 103
ERROR_RUNTIME = 104
ERROR_AI = 105
ERROR_DEPLOYMENT = 106
ERROR_MARKETPLACE = 107
ERROR_WORKSPACE = 108
ERROR_CRM = 109
ERROR_FILESYSTEM = 110

# ==============================================================================
# SUCCESS MESSAGES
# ==============================================================================

MSG_SUCCESS = "Operation completed successfully."
MSG_DEPLOY_SUCCESS = "Deployment completed."
MSG_BUILD_SUCCESS = "Compilation completed."
MSG_RUNTIME_STARTED = "Runtime started."
MSG_RUNTIME_STOPPED = "Runtime stopped."

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [

    "PLATFORM_NAME",
    "API_PREFIX",
    "CURRENT_VERSION",
    "TAG_SYSTEM",
    "TAG_REGISTRY",
    "TAG_BUILDER",
    "TAG_RUNTIME",
    "TAG_DEPLOYMENT",
    "TAG_MONITORING",
    "TAG_AI",
    "TAG_CRM",
    "TAG_WORKSPACE",
    "TAG_MARKETPLACE",
    "TAG_ADMIN",
    "TAG_HUMAN"

]
