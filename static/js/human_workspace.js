/*
═══════════════════════════════════════════════════════════════════════

GENESIS HR®
GEN-OS
Human Workspace Controller
BUILD 0200
Отвечает за:
• загрузку Workspace
• обновление данных
• события
• синхронизацию виджетов
• работу панели

═══════════════════════════════════════════════════════════════════════
*/

class HumanWorkspace {
    constructor() {
        this.workspace = null;
        this.profile = null;
        this.dashboard = [];
        this.loading = false;
        this.initialized = false;
        this.api = "/api/human/workspace";
        this.initialize();
    }

    // =====================================================
    // INITIALIZE
    // =====================================================

    async initialize() {
        console.log("[GEN-OS] Human Workspace");
        await this.load();
        this.bindEvents();
        this.initialized = true;
    }

    // =====================================================
    // LOAD
    // =====================================================

    async load() {
        try {
            this.loading = true;
            this.showLoading();
            const response = await fetch(this.api);
            if (!response.ok)
                throw new Error("Workspace loading failed");
            this.workspace = await response.json();
            this.profile = this.workspace.profile || {};
            this.dashboard = this.workspace.dashboard || [];
            this.render();
        }
        catch (error) {
            console.error(error);
            this.showError(error);
        }
        finally {
            this.loading = false;
            this.hideLoading();
        }
    }

    // =====================================================
    // REFRESH
    // =====================================================

    async refresh() {
        console.log("Refresh workspace");
        await this.load();
    }

    // =====================================================
    // RENDER
    // =====================================================

    render() {
        this.renderHeader();
        this.renderDashboard();
        this.renderProfile();
        this.renderCompetencies();
        this.renderProfessions();
        this.renderRisks();
        this.renderRoadmap();
    }

    // =====================================================
    // HEADER
    // =====================================================

    renderHeader() {
        const title = document.querySelector("[data-human-title]");
        if (!title)
            return;
        title.textContent =
            this.profile.fullname || "Human";

    }

    // =====================================================
    // DASHBOARD
    // =====================================================

    renderDashboard() {
        console.log("Dashboard", this.dashboard);
    }

    // =====================================================
    // PROFILE
    // =====================================================

    renderProfile() {
        console.log("Profile", this.profile);
    }

    // =====================================================
    // COMPETENCIES
    // =====================================================

    renderCompetencies() {
        console.log(
            this.workspace.competencies
        );
    }

    // =====================================================
    // PROFESSIONS
    // =====================================================

    renderProfessions() {
        console.log(
            this.workspace.professions
        );
    }

    // =====================================================
    // RISKS
    // =====================================================

    renderRisks() {
        console.log(
            this.workspace.risks
        );
    }

    // =====================================================
    // ROADMAP
    // =====================================================

    renderRoadmap() {
        console.log(
            this.workspace.roadmap
        );

    }

    // =====================================================
    // EVENTS
    // =====================================================

    bindEvents() {
        document.addEventListener(
            "workspace.refresh",
            () => this.refresh()
        );
    }

    // =====================================================
    // UI
    // =====================================================

    showLoading() {
        document.body.classList.add(
            "workspace-loading"
        );
    }

    hideLoading() {
        document.body.classList.remove(
            "workspace-loading"
        );
    }

    showError(error) {
        console.error(error);
    }

    // =====================================================
    // EXPORT
    // =====================================================

    export() {
        console.log(
            "Export workspace"
        );
    }

    // =====================================================
    // REPORT
    // =====================================================

    report() {
        console.log(
            "Generate report"
        );
    }
}

window.HumanWorkspace = HumanWorkspace;

window.addEventListener(

    "DOMContentLoaded",

    () => {

        window.humanWorkspace =
            new HumanWorkspace();

    }

);