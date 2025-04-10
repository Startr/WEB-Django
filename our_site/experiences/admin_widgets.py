from django import forms
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
import datetime
import json

class YearSelectorWidget(forms.Widget):
    """
    A custom widget that displays a list of checkboxes for year selection.
    Converts between a JSON list of years and a user-friendly checkbox interface.
    """
    template_name = 'admin/widgets/year_selector.html'

    def __init__(self, attrs=None, year_range=None):
        super().__init__(attrs)
        self.year_range = year_range or 10  # Default to showing 10 years

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Convert value from JSON list [2020, 2024, 2025] to a list of years if it exists
        current_years = set()
        if value:
            if isinstance(value, list):
                current_years = set(value)
            else:
                try:
                    # Handle case when it might come in as a string
                    current_years = set(json.loads(value))
                except (TypeError, json.JSONDecodeError):
                    current_years = set()
        
        # Generate a range of years to show
        current_year = datetime.datetime.now().year
        years = list(range(current_year - self.year_range, current_year + 5))
        
        year_choices = []
        for year in sorted(years, reverse=True):  # Show newest years first
            year_choices.append({
                'year': year,
                'checked': year in current_years,
            })
        
        context['widget']['year_choices'] = year_choices
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        
        # Create HTML directly since we don't have a template
        html = '<div class="year-selector">'
        html += f'<input type="hidden" name="{name}" id="id_{name}" value="">'
        html += '<div style="display: flex; flex-wrap: wrap; gap: 8px; max-width: 600px;">'
        
        for choice in context['widget']['year_choices']:
            checked = 'checked' if choice['checked'] else ''
            html += f'''
            <div style="flex: 0 0 80px;">
                <label style="display: flex; align-items: center;">
                    <input type="checkbox" name="{name}_year" value="{choice['year']}" {checked}
                           onchange="updateYearValues('{name}')">
                    <span style="margin-left: 5px;">{choice['year']}</span>
                </label>
            </div>
            '''
        
        html += '</div>'
        html += f'''
        <script>
        function updateYearValues(fieldName) {{
            const checkboxes = document.querySelectorAll(`input[name="${{fieldName}}_year"]:checked`);
            const years = Array.from(checkboxes).map(cb => parseInt(cb.value));
            document.getElementById(`id_${{fieldName}}`).value = JSON.stringify(years);
        }}
        // Initialize the value when the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            updateYearValues('{name}');
        }});
        </script>
        '''
        html += '</div>'
        
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        # Extract the year values from checkboxes and return as a list
        year_values = data.getlist(f"{name}_year")
        if not year_values:
            return json.dumps([])  # Return empty JSON array as string
        
        # Convert to JSON string instead of Python list
        return json.dumps([int(year) for year in year_values])