# FastForm - Data Expansion Guide

## 🏥 Add More Formularies

### Current Coverage (6 formularies):
- Medicare Part D Standard ✅
- Aetna Better Health ✅  
- Blue Cross Blue Shield ✅
- UnitedHealthcare Choice Plus ✅
- Humana Gold Plus ✅
- Cigna HealthCare ✅

### 🎯 Target Expansion (20+ more):
- **Anthem** - Major multi-state insurer
- **Kaiser Permanente** - Large HMO system
- **Molina Healthcare** - Medicaid specialist
- **Centene** - Government programs focus
- **CVS Health/Aetna** - Pharmacy integrated
- **State Medicaid Plans** - 50 state programs
- **Medicare Advantage** - Hundreds of plans
- **Employer Plans** - Corporate formularies

## 💊 Expand Drug Database

### Current: 78+ drugs → Target: 5,000+ drugs

### Priority Drug Categories:
```sql
-- High-impact therapeutic areas
INSERT INTO drugs (name, generic_name, category) VALUES
('Ozempic', 'semaglutide', 'Diabetes'),
('Keytruda', 'pembrolizumab', 'Oncology'),  
('Eliquis', 'apixaban', 'Anticoagulants'),
('Jardiance', 'empagliflozin', 'Diabetes'),
('Dupixent', 'dupilumab', 'Immunology');
```

### 📊 Data Sources:
- **CMS Orange Book** - FDA approved drugs
- **Medicare Part D** - Coverage databases  
- **State Medicaid** - Public formularies
- **Pharmacy chains** - Retail pricing
- **Clinical databases** - Drug interactions

## 🤖 Automated Data Pipeline

### Web Scraping Setup:
```python
# scripts/formulary_scraper.py
import requests
import sqlite3
from bs4 import BeautifulSoup

def scrape_medicare_formulary():
    # Scrape CMS.gov formulary data
    # Parse PDF/Excel files
    # Update database automatically
    pass

def update_drug_prices():
    # GoodRx API integration
    # Medicare pricing data
    # Insurance negotiated rates
    pass
```

### 🔄 Auto-Update System:
- **Daily**: Price updates
- **Weekly**: New drug approvals  
- **Monthly**: Formulary changes
- **Quarterly**: Major plan updates

## 🎯 Target: 50+ Formularies, 10,000+ Drugs
Your FastForm database could become the most comprehensive drug coverage platform! 📈
