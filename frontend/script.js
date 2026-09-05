/**
 * ResolveAI - Customer Support Resolution Assistant Dashboard Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const customerSelect = document.getElementById('customer-select');
    const customerSummary = document.getElementById('customer-summary');
    const queryInput = document.getElementById('query-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const btnSpinner = document.getElementById('btn-spinner');
    const errorBanner = document.getElementById('error-banner');

    const resultCard = document.getElementById('result-card');
    const decisionBadge = document.getElementById('decision-badge');
    const intentBadge = document.getElementById('intent-badge');
    const decisionReason = document.getElementById('decision-reason');
    const aiResponseText = document.getElementById('ai-response-text');
    const copyBtn = document.getElementById('copy-btn');
    const resolveStatusTag = document.getElementById('resolve-status-tag');

    const askPanel = document.getElementById('ask-panel');
    const missingInfoList = document.getElementById('missing-info-list');

    const escalatePanel = document.getElementById('escalate-panel');
    const escalateFactsList = document.getElementById('escalate-facts-list');
    const escalateAttemptsList = document.getElementById('escalate-attempts-list');

    const evidenceContainer = document.getElementById('evidence-container');
    const knowledgeSourceContainer = document.getElementById('knowledge-source-container');

    let customersCache = [];

    // 1. Load All Customers from Backend API
    initCustomerSelect();

    async function initCustomerSelect() {
        try {
            const res = await fetch('/api/customers');
            if (res.ok) {
                customersCache = await res.json();
                populateCustomerDropdown(customersCache);
            } else {
                showError("Failed to fetch customer list from backend.");
            }
        } catch (err) {
            showError("Unable to connect to ResolveAI backend server.");
        }
    }

    function populateCustomerDropdown(customers) {
        customerSelect.innerHTML = '<option value="">-- Select Customer --</option>';
        customers.forEach(cust => {
            const opt = document.createElement('option');
            opt.value = cust.customer_id;
            opt.textContent = `${cust.customer_id} - ${cust.name} (${cust.plan})`;
            customerSelect.appendChild(opt);
        });
    }

    // 2. Customer Selection Change Handler
    customerSelect.addEventListener('change', () => {
        const selectedId = customerSelect.value;
        hideError();
        
        if (!selectedId) {
            customerSummary.innerHTML = '<p class="text-muted">Select a customer from the dropdown to load verified account records.</p>';
            return;
        }

        const customer = customersCache.find(c => c.customer_id === selectedId);
        if (customer) {
            renderCustomerSummary(customer);
        } else {
            fetchCustomerDetail(selectedId);
        }
    });

    async function fetchCustomerDetail(customerId) {
        try {
            const res = await fetch(`/api/customers/${customerId}`);
            if (res.ok) {
                const customer = await res.json();
                renderCustomerSummary(customer);
            } else {
                customerSummary.innerHTML = `<p class="text-muted" style="color: var(--color-escalate);">Customer ${customerId} details not found.</p>`;
            }
        } catch (err) {
            customerSummary.innerHTML = `<p class="text-muted" style="color: var(--color-escalate);">Error loading customer profile.</p>`;
        }
    }

    function renderCustomerSummary(cust) {
        const connBadgeClass = cust.connection_status === 'active' ? 'color-resolve' : 'color-escalate';
        const billBadgeClass = cust.billing_status === 'paid' ? 'color-resolve' : 'color-ask';

        customerSummary.innerHTML = `
            <div class="context-row">
                <span class="context-label">Name</span>
                <span class="context-value">${escapeHtml(cust.name)}</span>
            </div>
            <div class="context-row">
                <span class="context-label">Customer ID</span>
                <span class="context-value">${escapeHtml(cust.customer_id)}</span>
            </div>
            <div class="context-row">
                <span class="context-label">Plan</span>
                <span class="context-value">${escapeHtml(cust.plan)}</span>
            </div>
            <div class="context-row">
                <span class="context-label">Current Bill</span>
                <span class="context-value">$${cust.current_bill}</span>
            </div>
            <div class="context-row">
                <span class="context-label">Billing</span>
                <span class="context-value" style="color: var(--${billBadgeClass});">${escapeHtml(cust.billing_status)}</span>
            </div>
            <div class="context-row">
                <span class="context-label">Connection</span>
                <span class="context-value" style="color: var(--${connBadgeClass});">${escapeHtml(cust.connection_status)}</span>
            </div>
        `;
    }

    // 3. Analyze Request Click Handler
    analyzeBtn.addEventListener('click', async () => {
        const customerId = customerSelect.value;
        const query = queryInput.value.trim();

        hideError();

        if (!customerId) {
            showError("Please select a customer before analyzing.");
            return;
        }

        if (!query) {
            showError("Please describe the customer's issue.");
            return;
        }

        // Set Loading State
        setLoadingState(true);

        try {
            const res = await fetch('/api/resolve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    customer_id: customerId,
                    query: query
                })
            });

            if (res.ok) {
                const data = await res.json();
                renderResolutionResults(data);
            } else {
                showError("Backend processing failed. Please check your query or server logs.");
            }
        } catch (err) {
            showError("Connection error while sending request to backend.");
        } finally {
            setLoadingState(false);
        }
    });

    // 4. Render Resolution Results
    function renderResolutionResults(data) {
        resultCard.classList.remove('hidden');

        // Decision Badge
        const decision = data.decision || 'ESCALATE';
        decisionBadge.textContent = decision;
        decisionBadge.className = `badge badge-${decision.toLowerCase()}`;

        // Intent Badge
        if (data.intent) {
            intentBadge.textContent = data.intent;
            intentBadge.classList.remove('hidden');
        } else {
            intentBadge.classList.add('hidden');
        }

        // Decision Rationale
        decisionReason.textContent = data.reasoning || 'Decision generated by deterministic rule engine.';

        // AI Response Text
        aiResponseText.textContent = data.response_text || 'No response generated.';

        // Panels Reset
        resolveStatusTag.classList.add('hidden');
        askPanel.classList.add('hidden');
        escalatePanel.classList.add('hidden');

        // Decision Specific Panels
        if (decision === 'RESOLVE') {
            resolveStatusTag.classList.remove('hidden');
        } else if (decision === 'ASK') {
            askPanel.classList.remove('hidden');
            renderList(missingInfoList, data.missing_information, "No missing details specified.");
        } else if (decision === 'ESCALATE') {
            escalatePanel.classList.remove('hidden');
            renderList(escalateFactsList, data.escalation_facts, "No specific escalation facts logged.");
            renderList(escalateAttemptsList, data.previous_attempts, "None logged.");
        }

        // Evidence
        renderEvidence(data.evidence);

        // Knowledge Source
        renderKnowledgeSource(data.article_id, data.article_title);
    }

    function renderList(container, items, emptyText) {
        container.innerHTML = '';
        if (items && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                container.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = emptyText;
            li.style.color = 'var(--text-muted)';
            container.appendChild(li);
        }
    }

    function renderEvidence(evidenceItems) {
        evidenceContainer.innerHTML = '';
        if (evidenceItems && evidenceItems.length > 0) {
            evidenceItems.forEach(item => {
                const div = document.createElement('div');
                div.className = 'evidence-item';
                div.textContent = item;
                evidenceContainer.appendChild(div);
            });
        } else {
            evidenceContainer.innerHTML = '<p class="text-muted">No specific account evidence returned.</p>';
        }
    }

    function renderKnowledgeSource(articleId, articleTitle) {
        if (articleId) {
            knowledgeSourceContainer.innerHTML = `
                <div class="source-item">
                    <div class="source-id">${escapeHtml(articleId)}</div>
                    <div class="source-title">${escapeHtml(articleTitle || 'Support Article')}</div>
                </div>
            `;
        } else {
            knowledgeSourceContainer.innerHTML = '<p class="text-muted">No knowledge article matched this request.</p>';
        }
    }

    // Copy Response Button Handler
    copyBtn.addEventListener('click', () => {
        const text = aiResponseText.textContent;
        if (!text) return;

        navigator.clipboard.writeText(text).then(() => {
            const orig = copyBtn.textContent;
            copyBtn.textContent = 'Copied! ✓';
            setTimeout(() => { copyBtn.textContent = orig; }, 2000);
        }).catch(() => {
            alert('Failed to copy response text.');
        });
    });

    // Helper functions
    function setLoadingState(isLoading) {
        analyzeBtn.disabled = isLoading;
        if (isLoading) {
            btnSpinner.classList.remove('hidden');
            analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing customer request...';
        } else {
            btnSpinner.classList.add('hidden');
            analyzeBtn.querySelector('.btn-text').textContent = 'Analyze Request';
        }
    }

    function showError(msg) {
        errorBanner.textContent = msg;
        errorBanner.classList.remove('hidden');
    }

    function hideError() {
        errorBanner.classList.add('hidden');
        errorBanner.textContent = '';
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
