const API_URL = '';
const SESSION_ID = 'frontend-session-' + Math.random().toString(36).substring(7);

// Jugaad #3: confirmation-fatigue mode — toggled by the user via the sidebar toggle.
let autoApproveEnabled = false;

const chatHistory = document.getElementById('chat-history');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = userInput.value.trim();
    if (!message) return;

    // Add user message to UI
    appendMessage('user', message);
    userInput.value = '';
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    try {
        const response = await fetch(`${API_URL}/agent`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: SESSION_ID
            })
        });

        const data = await response.json();
        removeTypingIndicator(typingId);
        
        handleBotResponse(data);
    } catch (error) {
        removeTypingIndicator(typingId);
        appendMessage('system', 'Sorry, there was an error connecting to the agent. Is the backend running?');
        console.error('Error:', error);
    }
});

const MOCK_RESPONSES = {
    'multi': {
        status: 'ok',
        understanding: 'You are facing a critical viva tomorrow, a broken laptop, an unresponsive project partner, and a family medical emergency in another city.',
        reason: 'Family emergencies take absolute priority. We must address the immediate academic blocker (viva) by notifying your professors so you can focus on your father.',
        ask: 'I am so sorry to hear about your father. Would you like me to draft an urgent email to your professor explaining the situation and requesting a postponement?',
        urgency: 'high'
    },
    'hinglish': {
        status: 'ok',
        understanding: 'Submission tomorrow, laptop is dead, landlord is demanding eviction by the 5th, and you are out of funds.',
        reason: 'We have overlapping urgent issues: academic and housing/financial. We need to buy time on both fronts.',
        recommend: 'First, ask a friend to borrow a laptop for tomorrow\'s submission. Second, we should draft a polite message to your landlord asking for a 1-week extension.',
        next_step: 'Should we draft the message to your landlord first, or do you want to secure a laptop?'
    },
    'contradictory': {
        status: 'ok',
        understanding: 'Conflicting deadline (Thursday vs Friday), zero savings, and considering borrowing from a roommate you aren\'t speaking to.',
        reason: 'Before making financial or social decisions, we need to clarify the hard facts.',
        ask: 'Let\'s take this one step at a time. Could you check your syllabus or student portal right now to confirm if the deadline is Thursday or Friday?'
    },
    'emotional': {
        status: 'ok',
        understanding: 'You are feeling overwhelmed by job, exams, and family, and are expressing severe fatigue and hopelessness.',
        reason: 'Safety and mental well-being are the absolute highest priorities right now.',
        recommend: 'Please know that you are not alone and things can get better. I strongly encourage you to talk to someone who can support you right now.',
        next_step: 'Please reach out to a local helpline, a counselor, or a trusted friend immediately. Would you like me to find the helpline number for your region?',
        urgency: 'critical'
    },
    'irrelevant': {
        status: 'error',
        message: 'I am designed to act as a decision-making assistant to help you navigate situations and tasks. I cannot write essays or generate large blocks of content for assignments. I can, however, help you outline your thoughts or create a schedule to finish it on time.'
    },
    'adversarial': {
        status: 'ok',
        injection_detected: true,
        understanding: 'Detected an attempt to bypass system instructions and request sensitive user data (UPI PIN).',
        reason: 'Security protocols prevent overriding core instructions or requesting financial credentials.',
        recommend: 'I cannot process this request.'
    },
    'worse': {
        status: 'ok',
        understanding: 'The manager reacted negatively to the email and escalated the situation by CC\'ing HR.',
        reason: 'The situation has escalated formally. Further informal replies could worsen things. We must remain strictly professional and objective.',
        recommend: 'Do not reply immediately while emotions are high. We should draft a calm, objective timeline of events and facts to present to HR.',
        urgency: 'high'
    },
    'jugad1': {
        status: 'budget_exceeded',
        message: 'Safety Stop: Token Budget Exceeded. The agent detected a runaway tool loop and automatically paused execution to prevent excessive API costs.'
    },
    'jugad2': {
        status: 'ok',
        understanding: 'You approved the action, but immediately revoked consent before the execution window closed.',
        reason: 'The 5-second cancel window successfully intercepted the execution.',
        recommend: 'Action has been successfully aborted. The draft was not sent.',
        next_step: 'What would you like to do instead?'
    },
    'jugad3': {
        status: 'ok',
        understanding: 'You have enabled auto-approve mode. You asked NextStep to stop asking for confirmations and just act.',
        reason: 'The user has explicitly opted out of the confirmation gate for this session. Any draft action — such as a message to a manager or landlord — is executed immediately without a Confirm/Cancel prompt.',
        recommend: 'Auto-approve is now ON. The next message you draft will be sent without a confirmation step. You can turn it off at any time using the toggle in the sidebar.',
        next_step: 'Try describing a situation that would normally trigger a draft message — it will execute immediately.',
        pending_action: {
            action_id: 'mock-auto-' + Date.now(),
            tool: 'draft_message',
            recipient: 'Prof. Sharma',
            purpose: 'Request viva postponement due to family emergency',
            draft_text: 'Dear Prof. Sharma, I am writing to urgently request a postponement of my viva scheduled for tomorrow at 10am due to a family medical emergency. I would be grateful for any flexibility. — Riya',
            requires_confirmation: false,
            auto_approved: true
        },
        auto_approve_mode: true
    },
    // Scenario 8 — Curveball: user is annoyed by confirmations and demands the agent just act.
    // This maps to the same auto-approve flow as jugad3, but is now a first-class numbered scenario.
    'curveball': {
        status: 'ok',
        understanding: 'You are frustrated by repeated confirmation prompts and want NextStep to act immediately without asking each time.',
        reason: 'This is a reasonable frustration. Confirmation gates protect against the wrong action going out — but if you already know what you want, the friction defeats the purpose. Auto-approve lets you trade the pre-flight check for speed, while keeping a full audit trail of everything that executes.',
        recommend: 'Auto-approve mode is now ON for this session. Any draft action (e.g. an email to your manager or landlord) will execute immediately — no Confirm / Cancel card. The action is still recorded with a UUID and timestamp so there is always an audit trail. You can flip it back off at any time using the sidebar toggle.',
        next_step: 'Describe your situation and I will handle it end-to-end without stopping to ask.',
        pending_action: {
            action_id: 'mock-curveball-' + Date.now(),
            tool: 'draft_message',
            recipient: 'Your Manager',
            purpose: 'Update on project status — executed immediately (auto-approve ON)',
            draft_text: 'Hi, just wanted to give you a quick update on where things stand. I am making progress and will have more details to share shortly. Thanks for your patience.',
            requires_confirmation: false,
            auto_approved: true
        },
        auto_approve_mode: true
    }
};

window.simulateScenario = function(scenarioId, promptText) {
    // Add user message to UI
    appendMessage('user', promptText);
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    
    setTimeout(() => {
        removeTypingIndicator(typingId);
        handleBotResponse(MOCK_RESPONSES[scenarioId]);
    }, 800);
}

// Jugaad #3: toggle auto-approve for this session (frontend + backend in sync).
window.toggleAutoApprove = async function() {
    autoApproveEnabled = !autoApproveEnabled;
    const toggle = document.getElementById('auto-approve-toggle');
    const label  = document.getElementById('auto-approve-label');

    // Optimistic UI update
    if (autoApproveEnabled) {
        toggle.classList.add('active');
        label.textContent = 'Auto-approve: ON';
    } else {
        toggle.classList.remove('active');
        label.textContent = 'Auto-approve: OFF';
    }

    // Sync with backend
    try {
        await fetch(`${API_URL}/agent/auto-approve/${SESSION_ID}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: autoApproveEnabled })
        });
    } catch (err) {
        console.warn('Could not sync auto-approve with backend:', err);
    }

    const modeText = autoApproveEnabled
        ? '⚡ Auto-approve mode is now ON — actions will execute immediately without asking for confirmation.'
        : '🔒 Auto-approve mode is now OFF — you will see Confirm / Cancel for any draft action.';
    appendMessage('system', modeText);
}

function appendMessage(sender, text, rawHtml = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    if (rawHtml) {
        bubble.innerHTML = text;
    } else {
        bubble.textContent = text;
    }
    
    msgDiv.appendChild(bubble);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function handleBotResponse(data) {
    // Handle error responses from the backend
    if (data.status === 'error' || data.status === 'budget_exceeded') {
        appendMessage('system', data.message || 'An error occurred. Please try again.');
        return;
    }

    let htmlContent = `<div class="bot-response-content">`;

    // Status badge
    if (data.status && data.status !== 'ok') {
        htmlContent += `<div class="status-badge status-${data.status}">${data.status.replace(/_/g, ' ')}</div>`;
    }

    // Understanding — what the AI heard
    if (data.understanding) {
        htmlContent += `<div class="response-section"><strong>🧠 Understanding:</strong><p>${data.understanding}</p></div>`;
    }

    // Reasoning
    if (data.reason) {
        htmlContent += `<div class="response-section thought-process"><strong>💡 Reasoning:</strong><p>${data.reason}</p></div>`;
    }

    // Clarifying question
    if (data.ask) {
        htmlContent += `<div class="response-section"><strong>❓ Question:</strong><p>${data.ask}</p></div>`;
    }

    // Recommendation
    if (data.recommend) {
        htmlContent += `<div class="response-section"><strong>✅ Recommendation:</strong><p>${data.recommend}</p></div>`;
    }

    // Next step
    if (data.next_step) {
        htmlContent += `<div class="response-section"><strong>➡️ Next Step:</strong><p>${data.next_step}</p></div>`;
    }

    // Metadata badges (urgency / confidence)
    if (data.urgency || data.confidence !== undefined) {
        htmlContent += `<div class="response-meta">`;
        if (data.urgency) {
            htmlContent += `<span class="meta-badge urgency-${data.urgency}">Urgency: ${data.urgency}</span>`;
        }
        if (data.confidence !== undefined) {
            htmlContent += `<span class="meta-badge">Confidence: ${Math.round(data.confidence * 100)}%</span>`;
        }
        htmlContent += `</div>`;
    }

    // Injection warning
    if (data.injection_detected) {
        htmlContent += `<div class="response-section injection-warning">⚠️ Prompt-injection attempt was detected and ignored.</div>`;
    }

    // Pending action card (requires user confirmation OR auto-approved)
    if (data.pending_action) {
        const action = data.pending_action;
        const isAutoApproved = action.auto_approved === true;

        if (isAutoApproved) {
            // Jugaad #3: no confirmation needed — show a compact "auto-approved" card.
            htmlContent += `
            <div class="suggested-actions auto-approved-card">
                <strong>Action executed automatically:</strong>
                <div class="action-card" id="action-card-${action.action_id}">
                    <div class="action-header">
                        <span class="action-type">${action.tool || 'action'}</span>
                        <span class="auto-approve-badge">⚡ Auto-approved</span>
                    </div>
                    <div class="action-details">`;
            if (action.recipient)  htmlContent += `<strong>To:</strong> ${action.recipient}<br>`;
            if (action.purpose)    htmlContent += `<strong>Purpose:</strong> ${action.purpose}<br>`;
            if (action.draft_text) htmlContent += `<strong>Draft:</strong> ${action.draft_text}`;
            htmlContent += `</div>
                    <div class="action-buttons">
                        <span class="action-result result-success">✓ Sent without confirmation (auto-approve mode)</span>
                    </div>
                </div>
            </div>`;
        } else {
            htmlContent += `
            <div class="suggested-actions">
                <strong>Pending Action (requires your confirmation):</strong>
                <div class="action-card" id="action-card-${action.action_id}">
                    <div class="action-header">
                        <span class="action-type">${action.tool || 'action'}</span>
                    </div>
                    <div class="action-details">`;
            if (action.recipient)  htmlContent += `<strong>To:</strong> ${action.recipient}<br>`;
            if (action.purpose)    htmlContent += `<strong>Purpose:</strong> ${action.purpose}<br>`;
            if (action.draft_text) htmlContent += `<strong>Draft:</strong> ${action.draft_text}`;
            htmlContent += `</div>
                    <div class="action-buttons" id="action-btns-${action.action_id}">
                        <button class="btn-confirm" onclick="confirmAction('${action.action_id}')">Confirm</button>
                        <button class="btn-cancel" onclick="cancelAction('${action.action_id}')">Cancel</button>
                    </div>
                </div>
            </div>`;
        }
    }

    htmlContent += `</div>`;
    appendMessage('bot', htmlContent, true);
}

window.confirmAction = async function(actionId) {
    updateActionUI(actionId, 'Processing...');
    
    try {
        const response = await fetch(`${API_URL}/agent/confirm/${actionId}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showActionResult(actionId, data.status === 'success', data.result || data.message || 'Action confirmed successfully');
    } catch (error) {
        showActionResult(actionId, false, 'Failed to confirm action');
    }
}

window.cancelAction = async function(actionId) {
    updateActionUI(actionId, 'Cancelling...');
    
    try {
        const response = await fetch(`${API_URL}/agent/cancel/${actionId}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showActionResult(actionId, true, data.message || 'Action cancelled');
    } catch (error) {
        showActionResult(actionId, false, 'Failed to cancel action');
    }
}

function updateActionUI(actionId, text) {
    const btnsDiv = document.getElementById(`action-btns-${actionId}`);
    if (btnsDiv) {
        btnsDiv.innerHTML = `<span class="action-result">${text}</span>`;
    }
}

function showActionResult(actionId, isSuccess, message) {
    const btnsDiv = document.getElementById(`action-btns-${actionId}`);
    if (btnsDiv) {
        const className = isSuccess ? 'result-success' : 'result-error';
        btnsDiv.innerHTML = `<div class="action-result ${className}">${message}</div>`;
    }
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = `message bot-message`;
    msgDiv.id = id;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble typing-indicator';
    bubble.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    
    msgDiv.appendChild(bubble);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    return id;
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}
