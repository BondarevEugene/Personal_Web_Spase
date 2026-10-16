# ==============================================================================
# PROJECT: OMNIFACTORY PLATFORM
# MODULE: Enterprise Schemas
# FILE: api/schemas.py
#
# AUTHOR: Yevhenii Bondariev
# ARCHITECT: OpenAI GPT-5.5
#
# PURPOSE
# ------------------------------------------------------------------------------
# Единый контракт данных платформы.
#
# Все REST API используют ТОЛЬКО эти модели.
#
# Никаких dict.
#
# ==============================================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ==============================================================================
# SYSTEM
# ==============================================================================

class HealthResponse(BaseModel):
    status: str = "ONLINE"

    platform: str = "OMNIFACTORY"

    version: str = "2.0"

    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# CLIENT
# ==============================================================================

class ClientSchema(BaseModel):
    id: Optional[int] = None

    full_name: str = Field(
        ...,
        title="Full Name",
        description="Полное имя клиента."
    )

    company: str = Field(
        default=""
    )

    phone: str = Field(
        default=""
    )

    email: str = Field(
        default=""
    )

    bot_id: str = Field(
        default=""
    )

    notes: str = Field(
        default=""
    )


# ==============================================================================
# PROJECT
# ==============================================================================

class ProjectSchema(BaseModel):
    id: Optional[int] = None

    name: str

    description: str = ""

    owner: str = ""

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )


# ==============================================================================
# BUILD REQUEST
# ==============================================================================

class BuildRequest(BaseModel):
    project_name: str

    selected_nodes: list[str]

    target: str = "telegram"

    runtime: str = "python"

    docker: bool = False


# ==============================================================================
# DEPLOY REQUEST
# ==============================================================================

class DeployRequest(BaseModel):
    client_id: str

    telegram_token: str

    selected_nodes: list[str]


# ==============================================================================
# REGISTRY DOMAIN
# ==============================================================================
#
# Реестр когнитивных модулей платформы.
#
# Используется:
#
#   • Builder
#   • Runtime
#   • Marketplace
#   • AI Compiler
#
# ==============================================================================

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ModuleFieldSchema(BaseModel):
    """
    Поле конфигурации одного модуля.
    """

    key: str = Field(..., description="Идентификатор параметра")

    title: str = Field(..., description="Название параметра")

    field_type: str = Field(
        default="text",
        description="Тип элемента интерфейса"
    )

    default: Optional[str] = None

    required: bool = False


class ModuleSchema(BaseModel):
    """
    Описание одного модуля Builder.
    """

    id: str

    title: str

    category: str

    description: str = ""

    color: str = "#7c3aed"

    icon: str = "cube"

    version: str = "1.0"

    author: str = "OmniFactory"

    enabled: bool = True

    fields: List[ModuleFieldSchema] = Field(default_factory=list)


class RegistryCategorySchema(BaseModel):
    """
    Категория Builder.
    """

    title: str

    icon: str

    color: str

    modules: List[ModuleSchema] = Field(default_factory=list)


class RegistrySchema(BaseModel):
    """
    Полный реестр платформы.
    """

    version: str = "2.0"

    categories: Dict[str, RegistryCategorySchema]


# ==============================================================================
# BUILDER DOMAIN
# ==============================================================================

class BuilderNodePosition(BaseModel):
    x: float

    y: float


class BuilderNode(BaseModel):
    id: str

    module: str

    title: str

    position: BuilderNodePosition

    config: dict = Field(default_factory=dict)


class BuilderConnection(BaseModel):
    source: str

    target: str

    output: str = "output_1"

    input: str = "input_1"


class BuilderCanvas(BaseModel):
    name: str

    version: str = "1.0"

    nodes: List[BuilderNode] = Field(default_factory=list)

    connections: List[BuilderConnection] = Field(default_factory=list)


# ==============================================================================
# COMPILER DOMAIN
# ==============================================================================

class CompileRequest(BaseModel):
    client_id: str

    project_name: str

    graph: BuilderCanvas

    runtime: str = "python"

    target: str = "telegram"

    docker: bool = True


class CompileResponse(BaseModel):
    success: bool = True

    generated_files: List[str]

    build_time: float

    runtime: str


# ==============================================================================
# DEPLOYMENT DOMAIN
# ==============================================================================

class DeployEnvironment(BaseModel):
    python_version: str = "3.12"

    docker: bool = True

    redis: bool = False

    postgres: bool = False

    nginx: bool = False


class DeploySchema(BaseModel):
    client_id: str

    project_name: str

    environment: DeployEnvironment

    selected_modules: List[str]


class DeployStatus(BaseModel):
    deployment_id: str

    status: str

    url: Optional[str] = None

    container: Optional[str] = None

    started_at: Optional[str] = None


# ==============================================================================
# AI DOMAIN
# ==============================================================================
#
# Все структуры взаимодействия с искусственным интеллектом.
#
# Используется:
#
# • AI Assistant
# • Ollama
# • OpenAI
# • Claude
# • Gemini
# • Human Twin
#
# ==============================================================================

class AIModelSchema(BaseModel):
    """
    Описание доступной LLM модели.
    """

    id: str

    provider: str

    model: str

    description: str = ""

    enabled: bool = True

    local: bool = True

    max_tokens: int = 8192

    temperature: float = 0.3


class AIChatMessage(BaseModel):
    """
    Одно сообщение диалога.
    """

    role: str = Field(
        description="system | user | assistant"
    )

    content: str


class AIChatRequest(BaseModel):
    """
    Запрос к AI.
    """

    session_id: str

    tenant_id: str = "default"

    messages: list[AIChatMessage]

    model: str = "codellama"

    stream: bool = False


class AIChatResponse(BaseModel):
    success: bool = True

    answer: str

    model: str

    tokens: int = 0

    execution_time: float = 0.0


# ==============================================================================
# HUMAN TWIN DOMAIN
# ==============================================================================


class HumanTwinProfile(BaseModel):
    """
    Цифровой профиль человека.
    """
    id: str
    full_name: str
    birthday: str
    language: str = "ru"
    country: str = ""
    email: str = ""
    avatar: str = ""


class HumanTwinWorkspace(BaseModel):
    """
    Рабочее пространство Human Twin.
    """
    profile: HumanTwinProfile
    active_modules: list[str] = Field(default_factory=list)
    ai_models: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)


# ==============================================================================
# PERSONAL WORKSPACE DOMAIN
# ==============================================================================

class WorkspaceFile(BaseModel):
    id: str
    filename: str
    extension: str
    size: int
    created_at: datetime


class WorkspaceFolder(BaseModel):
    id: str
    title: str
    files: list[WorkspaceFile] = Field(default_factory=list)


class WorkspaceSchema(BaseModel):
    id: str
    owner: str
    folders: list[WorkspaceFolder] = Field(default_factory=list)


# ==============================================================================
# RUNTIME DOMAIN
# ==============================================================================

class RuntimeNode(BaseModel):
    id: str
    name: str
    status: str
    cpu: float
    ram: float
    uptime: str


class RuntimeSchema(BaseModel):
    runtime_id: str
    environment: str
    nodes: list[RuntimeNode] = Field(default_factory=list)


# ==============================================================================
# TELEMETRY DOMAIN
# ==============================================================================

class TelemetryMetric(BaseModel):
    cpu: float
    ram: float
    disk: float
    network: float


class TelemetryResponse(BaseModel):
    server: str
    timestamp: datetime
    metrics: TelemetryMetric


# ==============================================================================
# DOMAIN
# ==============================================================================

class DockerContainerSchema(BaseModel):
    id: str
    image: str
    container_name: str
    status: str
    ports: list[str] = Field(default_factory=list)
    created_at: str


class DockerRuntime(BaseModel):
    containers: list[DockerContainerSchema]


# ==============================================================================
# MONITORING DOMAIN
# ==============================================================================

class MonitoringEvent(BaseModel):
    level: str
    source: str
    message: str
    timestamp: datetime


class MonitoringResponse(BaseModel):
    events: list[MonitoringEvent]
    total: int


# ==============================================================================
# CRM DOMAIN
# ==============================================================================
#
# Enterprise CRM ядро платформы.
#
# Используется:
#
# • Admin Panel
# • Personal Workspace
# • Billing
# • Builder
# • Marketplace
#
# ==============================================================================

class CompanySchema(BaseModel):
    """
    Компания клиента.
    """
    id: int | None = None
    name: str
    legal_name: str = ""
    country: str = ""
    city: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClientSchema(BaseModel):
    """
    Клиент платформы.
    """
    id: int | None = None
    company_id: int | None = None
    full_name: str
    email: str = ""
    phone: str = ""
    telegram: str = ""
    bot_id: str = ""
    status: str = "ACTIVE"
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectSchema(BaseModel):
    id: int | None = None
    client_id: int
    title: str
    description: str = ""
    status: str = "DESIGN"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# TASKS
# ==============================================================================

class TaskSchema(BaseModel):
    id: int | None = None
    project_id: int
    title: str
    description: str = ""
    priority: str = "NORMAL"
    status: str = "TODO"
    assignee: str = ""
    deadline: datetime | None = None


# ==============================================================================
# LICENSES
# ==============================================================================

class LicenseSchema(BaseModel):
    id: str
    title: str
    license_type: str
    expires: datetime | None = None
    active: bool = True


# ==============================================================================
# SUBSCRIPTIONS
# ==============================================================================

class SubscriptionSchema(BaseModel):
    id: str
    title: str
    period: str
    amount: float
    active: bool = True


# ==============================================================================
# PAYMENTS
# ==============================================================================

class PaymentSchema(BaseModel):
    id: str
    client_id: int
    amount: float
    currency: str = "USD"
    status: str = "NEW"
    payment_provider: str = "WayForPay"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==============================================================================
# MARKETPLACE DOMAIN
# ==============================================================================


class MarketplaceCategory(BaseModel):
    id: str
    title: str
    icon: str
    color: str


class MarketplaceProduct(BaseModel):
    id: str
    category: str
    title: str
    description: str = ""
    version: str = "1.0"
    author: str = "OmniFactory"
    price: float
    currency: str = "USD"
    installed: bool = False
    icon: str = "cube"


class MarketplaceResponse(BaseModel):
    products: list[MarketplaceProduct]


# ==============================================================================
# REPORTS DOMAIN
# ==============================================================================

class ReportSchema(BaseModel):
    id: str
    title: str
    report_type: str
    generated_at: datetime
    file: str


# ==============================================================================
# EXPORT DOMAIN
# ==============================================================================

class ExportRequest(BaseModel):
    format: str
    project_id: int
    include_assets: bool = True
    include_sources: bool = True
    docker: bool = False


# ==============================================================================
# IMPORT DOMAIN
# ==============================================================================

class ImportRequest(BaseModel):
    workspace: str
    overwrite: bool = False


# ==============================================================================
# VERSION DOMAIN
# ==============================================================================

class VersionSchema(BaseModel):
    platform: str = "OMNIFACTORY"
    version: str = "2.0"
    api: str = "v1"
    compiler: str = "2.0"
    runtime: str = "2.0"
