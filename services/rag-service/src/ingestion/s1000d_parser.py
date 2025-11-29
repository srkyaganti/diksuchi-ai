import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class S1000DParser:
    """
    Parser for S1000D XML Data Modules.
    Extracts structure, content, and references while preserving the Data Module Code (DMC).
    """
    
    def __init__(self):
        self.namespaces = {
            # Add common S1000D namespaces if needed, usually they are default or specific to the project
        }

    def parse_data_module(self, xml_path: str) -> Dict:
        """
        Parses a single S1000D XML file.
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 1. Extract Identity (DMC)
            dm_ident = self._extract_dm_ident(root)
            title = self._extract_title(root)
            
            # 2. Extract Content
            content_blocks = self._extract_content(root, dm_ident)
            
            # 3. Extract References
            references = self._extract_references(root)
            
            return {
                "dm_id": dm_ident,
                "title": title,
                "content_blocks": content_blocks,
                "references": references,
                "metadata": {
                    "schema_ver": root.attrib.get("noNamespaceSchemaLocation", "unknown")
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to parse {xml_path}: {str(e)}")
            raise

    def _extract_dm_ident(self, root: ET.Element) -> str:
        """Constructs the unique Data Module Code (DMC)."""
        # Look for identAndStatusSection -> dmAddress -> dmIdent -> dmCode
        dm_code = root.find(".//dmCode")
        if dm_code is None:
            return "UNKNOWN_DMC"
            
        attribs = dm_code.attrib
        # Standard S1000D DMC format: MODEL-SYSTEM-SUB-ASSY-DISASSY-DISASSYVAR-INFOC-ITEMLOC
        components = [
            attribs.get("modelIdentCode", ""),
            attribs.get("systemDiffCode", ""),
            attribs.get("systemCode", ""),
            attribs.get("subSystemCode", ""),
            attribs.get("subSubSystemCode", ""),
            attribs.get("assyCode", ""),
            attribs.get("disassyCode", ""),
            attribs.get("disassyCodeVariant", ""),
            attribs.get("infoCode", ""),
            attribs.get("infoCodeVariant", ""),
            attribs.get("itemLocationCode", "")
        ]
        return "-".join([c for c in components if c])

    def _extract_title(self, root: ET.Element) -> str:
        title_node = root.find(".//dmTitle/techName")
        return title_node.text if title_node is not None else "Untitled"

    def _extract_content(self, root: ET.Element, dm_id: str) -> List[Dict]:
        """Extracts text content from levelled paragraphs."""
        blocks = []
        
        # Find the content section (usually 'content')
        content_root = root.find(".//content")
        if content_root is None:
            return blocks

        # Iterate through levelled paragraphs
        for i, levelled_para in enumerate(content_root.findall(".//levelledPara")):
            title_node = levelled_para.find("title")
            section_title = title_node.text if title_node is not None else f"Section {i+1}"
            
            # Gather all paragraph text
            paras = levelled_para.findall("para")
            text_content = "\n".join([p.text for p in paras if p.text])
            
            # Extract procedural steps if present
            steps = []
            for step in levelled_para.findall(".//proceduralStep"):
                step_para = step.find("para")
                if step_para is not None and step_para.text:
                    steps.append(step_para.text)
            
            if steps:
                text_content += "\n\nSteps:\n" + "\n".join([f"{j+1}. {s}" for j, s in enumerate(steps)])

            if text_content.strip():
                blocks.append({
                    "id": f"{dm_id}_sec_{i}",
                    "section_title": section_title,
                    "text": text_content,
                    "type": "procedure" if steps else "description"
                })
                
        return blocks

    def _extract_references(self, root: ET.Element) -> List[str]:
        """Extracts referenced Data Module Codes."""
        refs = []
        for ref in root.findall(".//dmRef"):
            dm_ref_ident = ref.find("dmRefIdent")
            if dm_ref_ident is not None:
                dm_code = dm_ref_ident.find("dmCode")
                if dm_code is not None:
                    # Reconstruct the referenced DMC string
                    # Simplified for brevity - in production, reuse the _extract_dm_ident logic
                    attribs = dm_code.attrib
                    ref_str = f"{attribs.get('modelIdentCode')}-{attribs.get('systemCode')}-{attribs.get('subSystemCode')}"
                    refs.append(ref_str)
        return refs
