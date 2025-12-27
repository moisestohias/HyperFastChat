Create a detailed plan (`Right-Sidebar-Plan.md`) for updateding the drop-down menus for the provider and model selection to be collapsable sidebar residing on the right side of the window, where the provider/model selection process provides much more details about the model like the context window or support input/output modalities, description, as well as inference parameters control eg top-k, top-p, etc. where the user should be able to set these.

Here is a example will be available in `providers_config.json` 
```json
    {
      "id": "bytedance-seed/seed-1.6-flash",
      "canonical_slug": "bytedance-seed/seed-1.6-flash-20250625",
      "hugging_face_id": "",
      "name": "ByteDance Seed: Seed 1.6 Flash",
      "created": 1766505011,
      "description": "Seed 1.6 Flash is an ultra-fast multimodal deep thinking model by ByteDance Seed, supporting both text and visual understanding. It features a 256k context window and can generate outputs of up to 16k tokens.",
      "context_length": 262144,
      "architecture": {
        "modality": "text+image->text",
        "input_modalities": [
          "image",
          "text",
          "video"
        ],
        "output_modalities": [
          "text"
        ],
        "tokenizer": "Other",
        "instruct_type": null
      },
      "pricing": {
        "prompt": "0.000000075",
        "completion": "0.0000003",
        "request": "0",
        "image": "0",
        "web_search": "0",
        "internal_reasoning": "0"
      },
      "top_provider": {
        "context_length": 262144,
        "max_completion_tokens": 16384,
        "is_moderated": false
      },
      "per_request_limits": null,
      "supported_parameters": [
        "frequency_penalty",
        "include_reasoning",
        "max_tokens",
        "reasoning",
        "response_format",
        "structured_outputs",
        "temperature",
        "tool_choice",
        "tools",
        "top_p"
      ],
      "default_parameters": {
        "temperature": null,
        "top_p": null,
        "frequency_penalty": null
      }
    },
```