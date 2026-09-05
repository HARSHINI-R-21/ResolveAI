/**
 * ResolveAI - Frontend Client Script
 * Handles Customer Lookup, Case Submission, and Rendering Decisions & Evidence.
 */

document.addEventListener('DOMContentLoaded', () => {
    const fetchCustomerBtn = document.getElementById('fetch-customer-btn');
    const customerIdInput = document.getElementById('customer-id-input');
    const profileContent = document.getElementById('profile-content');
    
    const submitQueryBtn = document.getElementById('submit-query-btn');
    const queryInput = document.getElementById('query-input');
    const categorySelect = document.getElementById('category-select');

    const decisionBadge = document.getElementById('decision-badge');
    const resultBody = document.getElementById('result-body');
    const evidenceContainer = document.getElementById('evidence-container');
    const articlesContainer = document.getElementById('articles-container');

    // Customer Lookup Placeholder Handler
    fetchCustomerBtn.addEventListener('click', async () => {
        const customerId = customerIdInput.value.trim();
        if (!customerId) {
            alert('Please enter a valid Customer ID.');
            return;
        }

        profileContent.innerHTML = `<p class="text-muted">Loading profile for ${customerId}...</p>`;
        
        try {
            const res = await fetch(`/api/customers/${customerId}`);
            if (res.ok) {
                const data = await res.json();
                renderCustomerProfile(data);
            } else {
                profileContent.innerHTML = `<p class="text-muted" style="color: var(--color-escalate);">Customer ${customerId} not found.</p>`;
            }
        } catch (err) {
            // Placeholder fallback when backend API is not yet implemented
            profileContent.innerHTML = `
                <div class="profile-details">
                    <p><strong>ID:</strong> ${customerId}</p>
                    <p class="text-muted">Backend API offline or in development.</p>
                </div>
            `;
        }
    });

    // Query Submission Placeholder Handler
    submitQueryBtn.addEventListener('click', async () => {
        const query = queryInput.value.trim();
        const category = categorySelect.value;
        const customerId = customerIdInput.value.trim();

        if (!query) {
            alert('Please enter a query description.');
            return;
        }

        resultBody.innerHTML = `<p class="placeholder-text">Analyzing query against verified account data and knowledge base...</p>`;

        try {
            const res = await fetch('/api/resolve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ customer_id: customerId, category, query })
            });

            if (res.ok) {
                const data = await res.json();
                renderResolutionResult(data);
            } else {
                renderPlaceholderResult(query, category);
            }
        } catch (err) {
            renderPlaceholderResult(query, category);
        }
    });

    function renderCustomerProfile(data) {
        profileContent.innerHTML = `
            <div class="profile-details">
                <p><strong>Name:</strong> ${data.name}</p>
                <p><strong>Service:</strong> ${data.service_type} (${data.plan_name})</p>
                <p><strong>Billing Status:</strong> ${data.billing_status}</p>
            </div>
        `;
    }

    function renderResolutionResult(data) {
        // Update Decision Badge
        decisionBadge.className = `badge badge-${data.decision.toLowerCase()}`;
        decisionBadge.textContent = data.decision;

        // Update Result Body
        resultBody.innerHTML = `<p class="placeholder-text">${data.response_text}</p>`;
    }

    function renderPlaceholderResult(query, category) {
        decisionBadge.className = 'badge badge-ask';
        decisionBadge.textContent = 'ASK';
        resultBody.innerHTML = `
            <p class="placeholder-text">
                [Placeholder Response]: To resolve your ${category} query ("${query}"), please provide the missing account verification details.
            </p>
        `;
    }
});
