import json
import yaml
from typing import Any, Dict, List, Optional
from pathlib import Path
from string import Template
import re
from dataclasses import dataclass, field
from enum import Enum

from ..utils import setup_logging


logger = setup_logging("LLM.Prompts")


class PromptType(str, Enum):
    """Types of prompts"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TEMPLATE = "template"
    CHAIN = "chain"


@dataclass
class PromptTemplate:
    """A reusable prompt template"""
    name: str
    template: str
    type: PromptType = PromptType.TEMPLATE
    description: Optional[str] = None
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables"""
        # Use Template for safe substitution
        tmpl = Template(self.template)
        
        # Check for missing variables
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            logger.warning(f"Missing variables for template '{self.name}': {missing}")
        
        # Perform substitution
        try:
            return tmpl.safe_substitute(**kwargs)
        except Exception as e:
            logger.error(f"Error formatting template '{self.name}': {e}")
            raise
    
    def extract_variables(self) -> List[str]:
        """Extract variable names from template"""
        # Find all $variable or ${variable} patterns
        pattern = r'\$\{?(\w+)\}?'
        variables = re.findall(pattern, self.template)
        return list(set(variables))
    
    def validate(self) -> bool:
        """Validate the template"""
        extracted = self.extract_variables()
        
        # Check if declared variables match extracted
        if set(self.variables) != set(extracted):
            logger.warning(
                f"Variable mismatch in template '{self.name}': "
                f"declared={self.variables}, extracted={extracted}"
            )
            self.variables = extracted
        
        return True


class PromptLibrary:
    """Library of reusable prompts"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default prompt templates"""
        defaults = {
            "summarize": PromptTemplate(
                name="summarize",
                template="Please summarize the following text in ${style} style:\n\n${text}",
                variables=["style", "text"],
                description="Summarize text in a specific style"
            ),
            "analyze": PromptTemplate(
                name="analyze",
                template="Analyze the following ${subject} and provide insights:\n\n${content}",
                variables=["subject", "content"],
                description="Analyze content and provide insights"
            ),
            "translate": PromptTemplate(
                name="translate",
                template="Translate the following text from ${source_lang} to ${target_lang}:\n\n${text}",
                variables=["source_lang", "target_lang", "text"],
                description="Translate text between languages"
            ),
            "extract": PromptTemplate(
                name="extract",
                template="Extract ${what} from the following text:\n\n${text}",
                variables=["what", "text"],
                description="Extract specific information from text"
            ),
            "qa": PromptTemplate(
                name="qa",
                template="Based on the following context:\n\n${context}\n\nAnswer this question: ${question}",
                variables=["context", "question"],
                description="Question answering based on context"
            ),
            "code_review": PromptTemplate(
                name="code_review",
                template="Review the following ${language} code and provide feedback:\n\n```${language}\n${code}\n```",
                variables=["language", "code"],
                description="Review code and provide feedback"
            ),
            "generate_code": PromptTemplate(
                name="generate_code",
                template="Generate ${language} code that ${task}:\n\nRequirements:\n${requirements}",
                variables=["language", "task", "requirements"],
                description="Generate code for a specific task"
            ),
        }
        
        for name, template in defaults.items():
            self.add_template(template)
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a template to the library"""
        template.validate()
        self.templates[template.name] = template
        logger.info(f"Added template: {template.name}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def format_template(self, name: str, **kwargs) -> str:
        """Format a template with variables"""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")
        
        return template.format(**kwargs)
    
    def list_templates(self) -> List[str]:
        """List all template names"""
        return list(self.templates.keys())
    
    def get_template_info(self, name: str) -> Dict[str, Any]:
        """Get information about a template"""
        template = self.get_template(name)
        if not template:
            return {}
        
        return {
            "name": template.name,
            "description": template.description,
            "variables": template.variables,
            "type": template.type.value,
            "metadata": template.metadata,
        }
    
    def load_from_file(self, file_path: Path) -> None:
        """Load templates from a YAML or JSON file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r") as f:
            if file_path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        for template_data in data.get("templates", []):
            template = PromptTemplate(
                name=template_data["name"],
                template=template_data["template"],
                type=PromptType(template_data.get("type", "template")),
                description=template_data.get("description"),
                variables=template_data.get("variables", []),
                metadata=template_data.get("metadata", {}),
            )
            self.add_template(template)
    
    def save_to_file(self, file_path: Path) -> None:
        """Save templates to a YAML or JSON file"""
        data = {
            "templates": [
                {
                    "name": t.name,
                    "template": t.template,
                    "type": t.type.value,
                    "description": t.description,
                    "variables": t.variables,
                    "metadata": t.metadata,
                }
                for t in self.templates.values()
            ]
        }
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            if file_path.suffix in [".yaml", ".yml"]:
                yaml.dump(data, f, default_flow_style=False)
            else:
                json.dump(data, f, indent=2)


class PromptChain:
    """Chain multiple prompts together"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
    
    def add_step(
        self,
        template_name: str,
        variables: Dict[str, Any],
        output_key: str,
    ) -> "PromptChain":
        """Add a step to the chain"""
        self.steps.append({
            "template": template_name,
            "variables": variables,
            "output_key": output_key,
        })
        return self
    
    async def execute(
        self,
        library: PromptLibrary,
        llm_client,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the prompt chain"""
        from .base import ChatMessage
        
        # Initialize context
        self.context = initial_context or {}
        results = {}
        
        for i, step in enumerate(self.steps):
            # Get template
            template_name = step["template"]
            template = library.get_template(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Prepare variables
            variables = {}
            for key, value in step["variables"].items():
                if isinstance(value, str) and value.startswith("$"):
                    # Reference to context variable
                    var_name = value[1:]
                    if var_name in self.context:
                        variables[key] = self.context[var_name]
                    elif var_name in results:
                        variables[key] = results[var_name]
                    else:
                        raise ValueError(f"Variable '{var_name}' not found in context")
                else:
                    variables[key] = value
            
            # Format prompt
            prompt = template.format(**variables)
            
            # Execute with LLM
            logger.info(f"Executing chain step {i+1}: {template_name}")
            
            if template.type == PromptType.SYSTEM:
                messages = [
                    ChatMessage(role="system", content=prompt),
                    ChatMessage(role="user", content="Please proceed."),
                ]
                response = await llm_client.chat(messages)
            else:
                response = await llm_client.generate(prompt)
            
            # Store result
            output_key = step["output_key"]
            results[output_key] = response.text
            self.context[output_key] = response.text
        
        return results


class PromptOptimizer:
    """Optimize prompts for better performance"""
    
    @staticmethod
    def optimize_for_model(prompt: str, model: str) -> str:
        """Optimize prompt for specific model"""
        # Model-specific optimizations
        if "gpt" in model.lower():
            # OpenAI GPT optimizations
            prompt = PromptOptimizer._add_gpt_instructions(prompt)
        elif "claude" in model.lower():
            # Anthropic Claude optimizations
            prompt = PromptOptimizer._add_claude_instructions(prompt)
        
        return prompt
    
    @staticmethod
    def _add_gpt_instructions(prompt: str) -> str:
        """Add GPT-specific instructions"""
        # GPT models respond well to clear structure
        if "step by step" not in prompt.lower():
            prompt += "\n\nPlease think step by step."
        return prompt
    
    @staticmethod
    def _add_claude_instructions(prompt: str) -> str:
        """Add Claude-specific instructions"""
        # Claude models respond well to politeness and clarity
        if not prompt.startswith("Please"):
            prompt = "Please " + prompt[0].lower() + prompt[1:]
        return prompt
    
    @staticmethod
    def add_output_format(prompt: str, format_type: str) -> str:
        """Add output format instructions"""
        format_instructions = {
            "json": "\n\nPlease format your response as valid JSON.",
            "markdown": "\n\nPlease format your response using Markdown.",
            "bullet": "\n\nPlease format your response as bullet points.",
            "numbered": "\n\nPlease format your response as a numbered list.",
        }
        
        instruction = format_instructions.get(format_type, "")
        if instruction and instruction not in prompt:
            prompt += instruction
        
        return prompt