# Right Sidebar Plan: Model Selection & Inference Parameters

## Overview

Replace the header dropdown menus with a **collapsible right sidebar** providing:
- Rich model selection with detailed metadata
- Inference parameter controls (temperature, top_p, etc.)
- Input/output modality indicators
- Context window & pricing info

---

## Data Model Updates

### Enhanced Provider Config Structure
Based on the provided example, update `providers_config.json`:

```json
{
  "openrouter": {
    "name": "OpenRouter",
    "api_base": "https://openrouter.ai/api/v1",
    "models": [
      {
        "id": "bytedance-seed/seed-1.6-flash",
        "name": "ByteDance Seed: Seed 1.6 Flash",
        "description": "Ultra-fast multimodal deep thinking model...",
        "context_length": 262144,
        "max_completion_tokens": 16384,
        "architecture": {
          "modality": "text+image->text",
          "input_modalities": ["image", "text", "video"],
          "output_modalities": ["text"]
        },
        "pricing": {
          "prompt": "0.000000075",
          "completion": "0.0000003"
        },
        "supported_parameters": [
          "temperature", "top_p", "top_k", "frequency_penalty", "max_tokens"
        ],
        "default_parameters": {
          "temperature": 0.7,
          "top_p": 0.95,
          "top_k": 40
        }
      }
    ]
  }
}
```

### Conversation Inference Parameters
Stored per-conversation in `chats[conv_id]`:

```python
{
  "inference_parameters": {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_tokens": 4096,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  }
}
```

---

## Backend Endpoints

### 1. Get Model Details
```python
@app.get("/models/{provider}/{model_id}", response_class=HTMLResponse)
async def get_model_details(request: Request, provider: str, model_id: str):
    """Returns detailed model info partial for right sidebar."""
    model = find_model(provider, model_id)
    return templates.TemplateResponse("model_details_card.html", {
        "request": request, "model": model, "provider": provider
    })
```

### 2. Update Inference Parameters
```python
class InferenceParamsModel(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

@app.patch("/chat/{conv_id}/inference-params", response_class=HTMLResponse)
async def update_inference_params(conv_id: str, data: InferenceParamsModel):
    """Update inference parameters for a conversation."""
    if conv_id not in chats:
        return HTMLResponse(status_code=404)
    
    params = chats[conv_id].setdefault("inference_parameters", {})
    for field, value in data.dict(exclude_none=True).items():
        params[field] = value
    write_db_to_disk()
    return HTMLResponse(content="OK")
```

### 3. Reset to Defaults
```python
@app.post("/chat/{conv_id}/inference-params/reset")
async def reset_inference_params(conv_id: str):
    """Reset inference parameters to model defaults."""
    model = get_current_model(conv_id)
    chats[conv_id]["inference_parameters"] = model["default_parameters"].copy()
    write_db_to_disk()
    return templates.TemplateResponse("inference_params_form.html", {...})
```

---

## Frontend Templates

### 1. `base.html` Updates
Add right sidebar container:

```html
<body class="bg-zinc-900 h-full flex overflow-hidden">
    <!-- Left Sidebar -->
    <div id="sidebar-container">...</div>
    
    <!-- Main Content -->
    <main class="flex-1 flex flex-col h-screen overflow-hidden">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Right Sidebar (NEW) -->
    <aside id="right-sidebar" 
        class="h-screen bg-[#0d0d0d] border-l border-gray-800 transition-all duration-300 ease-in-out right-sidebar-collapsed"
        _="on load if localStorage.rightSidebarStatus is 'expanded' 
              remove .right-sidebar-collapsed from me
              add .right-sidebar-expanded to me">
        {% include "right_sidebar.html" %}
    </aside>
    
    <!-- Right Sidebar Toggle -->
    <button id="right-sidebar-toggle"
        class="fixed top-4 right-4 z-50 p-2 rounded-lg bg-zinc-800/50 backdrop-blur-md..."
        _="on click toggle .right-sidebar-expanded .right-sidebar-collapsed on #right-sidebar
           if #right-sidebar.classList.contains('right-sidebar-expanded')
             set localStorage.rightSidebarStatus to 'expanded'
           else
             set localStorage.rightSidebarStatus to 'collapsed'">
        <svg><!-- Settings gear icon --></svg>
    </button>
</body>
```

### 2. New `right_sidebar.html`

```html
<div id="right-sidebar-content" class="h-full flex flex-col overflow-hidden p-4">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-white">Model Settings</h2>
        <button class="text-gray-400 hover:text-white" 
            _="on click add .right-sidebar-collapsed to #right-sidebar
               remove .right-sidebar-expanded from #right-sidebar">
            <svg class="w-5 h-5"><!-- X icon --></svg>
        </button>
    </div>

    <!-- Provider Selection -->
    <div class="mb-4">
        <label class="text-xs text-gray-500 uppercase tracking-wider mb-2 block">Provider</label>
        <div id="provider-select" class="space-y-1">
            {% for p_id, p_config in providers_config.items() %}
            <button class="provider-btn w-full text-left px-3 py-2 rounded-lg text-sm
                {{ 'bg-blue-600/20 text-blue-400 border border-blue-500/50' if p_id == current_provider 
                   else 'bg-zinc-800 text-gray-300 hover:bg-zinc-700' }}"
                data-provider="{{ p_id }}"
                _="on click 
                    take .bg-blue-600/20 .text-blue-400 from .provider-btn
                    add .bg-blue-600/20 .text-blue-400 to me
                    -- Load models for this provider
                    htmx.ajax('GET', '/partials/model-list?provider={{ p_id }}', '#model-list')">
                {{ p_config.name }}
            </button>
            {% endfor %}
        </div>
    </div>

    <!-- Model Selection -->
    <div class="mb-4 flex-shrink-0">
        <label class="text-xs text-gray-500 uppercase tracking-wider mb-2 block">Model</label>
        <div id="model-list" class="space-y-1 max-h-48 overflow-y-auto custom-scrollbar">
            {% include "right_sidebar_model_list.html" %}
        </div>
    </div>

    <!-- Model Details Card -->
    <div id="model-details" class="mb-4 p-3 bg-zinc-800/50 rounded-xl border border-gray-700">
        {% include "model_details_card.html" %}
    </div>

    <!-- Inference Parameters -->
    <div class="flex-1 overflow-y-auto custom-scrollbar">
        <div class="flex items-center justify-between mb-3">
            <label class="text-xs text-gray-500 uppercase tracking-wider">Parameters</label>
            <button class="text-xs text-blue-400 hover:text-blue-300"
                hx-post="/chat/{{ conversation_id }}/inference-params/reset"
                hx-target="#inference-params-form">
                Reset to Default
            </button>
        </div>
        <div id="inference-params-form">
            {% include "inference_params_form.html" %}
        </div>
    </div>
</div>
```

### 3. New `model_details_card.html`

```html
<div class="space-y-3">
    <!-- Model Name -->
    <div>
        <h3 class="text-sm font-medium text-white">{{ model.name }}</h3>
        <p class="text-xs text-gray-500 mt-1">{{ model.id }}</p>
    </div>

    <!-- Description -->
    {% if model.description %}
    <p class="text-xs text-gray-400 leading-relaxed">{{ model.description[:150] }}...</p>
    {% endif %}

    <!-- Modalities -->
    <div class="flex flex-wrap gap-2">
        {% for modality in model.architecture.input_modalities %}
        <span class="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">
            📥 {{ modality }}
        </span>
        {% endfor %}
        {% for modality in model.architecture.output_modalities %}
        <span class="px-2 py-0.5 text-xs rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
            📤 {{ modality }}
        </span>
        {% endfor %}
    </div>

    <!-- Context & Tokens -->
    <div class="grid grid-cols-2 gap-2 text-xs">
        <div class="bg-zinc-900 rounded-lg p-2">
            <span class="text-gray-500">Context</span>
            <p class="text-white font-mono">{{ (model.context_length / 1024) | int }}K</p>
        </div>
        <div class="bg-zinc-900 rounded-lg p-2">
            <span class="text-gray-500">Max Output</span>
            <p class="text-white font-mono">{{ (model.max_completion_tokens / 1024) | int }}K</p>
        </div>
    </div>

    <!-- Pricing -->
    {% if model.pricing %}
    <div class="text-xs text-gray-500">
        <span>💰 ${{ model.pricing.prompt }}/1K in</span> · 
        <span>${{ model.pricing.completion }}/1K out</span>
    </div>
    {% endif %}
</div>
```

### 4. New `inference_params_form.html`

```html
<div class="space-y-4">
    <!-- Temperature -->
    <div class="param-control">
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-300">Temperature</label>
            <span id="temp-value" class="text-xs text-gray-500 font-mono">{{ params.temperature or 0.7 }}</span>
        </div>
        <input type="range" name="temperature" min="0" max="2" step="0.1" 
            value="{{ params.temperature or 0.7 }}"
            class="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer slider"
            hx-patch="/chat/{{ conversation_id }}/inference-params"
            hx-trigger="change"
            hx-ext="json-enc"
            _="on input put my value into #temp-value">
        <div class="flex justify-between text-[10px] text-gray-600 mt-1">
            <span>Precise</span><span>Creative</span>
        </div>
    </div>

    <!-- Top P -->
    <div class="param-control">
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-300">Top P</label>
            <span id="topp-value" class="text-xs text-gray-500 font-mono">{{ params.top_p or 0.95 }}</span>
        </div>
        <input type="range" name="top_p" min="0" max="1" step="0.05"
            value="{{ params.top_p or 0.95 }}"
            class="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer slider"
            hx-patch="/chat/{{ conversation_id }}/inference-params"
            hx-trigger="change"
            hx-ext="json-enc"
            _="on input put my value into #topp-value">
    </div>

    <!-- Top K (if supported) -->
    {% if 'top_k' in supported_parameters %}
    <div class="param-control">
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-300">Top K</label>
            <span id="topk-value" class="text-xs text-gray-500 font-mono">{{ params.top_k or 40 }}</span>
        </div>
        <input type="range" name="top_k" min="1" max="100" step="1"
            value="{{ params.top_k or 40 }}"
            class="w-full h-2 bg-zinc-700 rounded-lg"
            hx-patch="/chat/{{ conversation_id }}/inference-params"
            hx-trigger="change"
            hx-ext="json-enc"
            _="on input put my value into #topk-value">
    </div>
    {% endif %}

    <!-- Max Tokens -->
    <div class="param-control">
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-300">Max Tokens</label>
            <input type="number" id="max-tokens-input" name="max_tokens"
                value="{{ params.max_tokens or 4096 }}"
                class="w-20 bg-zinc-800 text-white text-xs text-right px-2 py-1 rounded border border-gray-700"
                hx-patch="/chat/{{ conversation_id }}/inference-params"
                hx-trigger="change"
                hx-ext="json-enc">
        </div>
    </div>

    <!-- Frequency Penalty -->
    <div class="param-control">
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-300">Frequency Penalty</label>
            <span id="freq-value" class="text-xs text-gray-500 font-mono">{{ params.frequency_penalty or 0 }}</span>
        </div>
        <input type="range" name="frequency_penalty" min="-2" max="2" step="0.1"
            value="{{ params.frequency_penalty or 0 }}"
            class="w-full h-2 bg-zinc-700 rounded-lg"
            hx-patch="/chat/{{ conversation_id }}/inference-params"
            hx-trigger="change"
            hx-ext="json-enc"
            _="on input put my value into #freq-value">
    </div>
</div>
```

---

## CSS Additions (`style.css`)

```css
/* Right Sidebar */
.right-sidebar-expanded {
    width: 320px;
}

.right-sidebar-collapsed {
    width: 0;
    overflow: hidden;
}

#right-sidebar {
    background-color: #0d0d0d;
}

/* Custom Range Slider */
.slider::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: #3b82f6;
    border-radius: 50%;
    cursor: pointer;
    transition: transform 0.1s;
}

.slider::-webkit-slider-thumb:hover {
    transform: scale(1.2);
}

.slider::-webkit-slider-thumb:active {
    background: #2563eb;
}

/* Parameter control styling */
.param-control {
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(75, 85, 99, 0.3);
}
```

---

## Implementation Phases

| Phase | Tasks | Files |
|-------|-------|-------|
| **1** | Update `providers_config.json` schema with full model metadata | `LLMConnect/providers_config.json` |
| **2** | Add backend endpoints for params & model details | `main.py` |
| **3** | Create right sidebar structure | `base.html`, `right_sidebar.html` |
| **4** | Create model details card | `model_details_card.html` |
| **5** | Create inference params form | `inference_params_form.html` |
| **6** | Add CSS for sidebar & sliders | `style.css` |
| **7** | Wire up LLMConnect to use params | `main.py` (run_chatbot_logic) |

---

## Wire Inference Params to LLM

Update `run_chatbot_logic()` to pass parameters:

```python
async def run_chatbot_logic(conv_id: str):
    # ... existing setup ...
    
    inference_params = chats[conv_id].get("inference_parameters", {})
    
    stream = await client.chat(
        history_to_send, 
        stream=True,
        temperature=inference_params.get("temperature"),
        top_p=inference_params.get("top_p"),
        max_tokens=inference_params.get("max_tokens"),
        # ... other params
    )
```

---

## Summary

| Component | Status | Priority |
|-----------|--------|----------|
| `providers_config.json` schema | New structure | P0 |
| Right sidebar container | New | P0 |
| Model details card | New partial | P0 |
| Inference params form | New partial | P0 |
| Backend param endpoints | 3 new routes | P0 |
| CSS slider styling | New styles | P1 |
| LLMConnect integration | Update | P1 |

**Estimated Effort**: 3-4 hours
