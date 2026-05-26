import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

VENDORS = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

MOCK_DATA = {
    "google": [
        {
            "name": "Sundar Pichai",
            "title": "CEO",
            "since": "2015",
            "bio": "Joined Google in 2004; previously led product management and innovation for Chrome, Google Drive, Google Maps, and Android."
        },
        {
            "name": "Ruth Porat",
            "title": "President, Chief Investment Officer & CFO",
            "since": "2015",
            "bio": "Oversees Alphabet's global finance, corporate development, and technology investments; previously EVP and CFO at Morgan Stanley."
        },
        {
            "name": "Philipp Schindler",
            "title": "SVP and Chief Business Officer",
            "since": "2015",
            "bio": "Responsible for all global sales, operations, customer service, and partnerships; previously oversaw business operations in Europe."
        },
        {
            "name": "Prabhakar Raghavan",
            "title": "SVP, Search, Assistant and Geo",
            "since": "2020",
            "bio": "Heads search engine, assistant, and maps development; previously led Google Apps, Yahoo! Labs, and IBM research pipelines."
        },
        {
            "name": "Kent Walker",
            "title": "President, Global Affairs & Chief Legal Officer",
            "since": "2018",
            "bio": "Oversees public policy, legal affairs, trust, and safety; previously Associate General Counsel at Netscape and AOL."
        },
        {
            "name": "Thomas Kurian",
            "title": "CEO, Google Cloud",
            "since": "2019",
            "bio": "Drives Alphabet's enterprise cloud growth; previously spent 22 years at Oracle as President of Product Development."
        }
    ],
    "microsoft": [
        {
            "name": "Satya Nadella",
            "title": "Chairman and CEO",
            "since": "2014",
            "bio": "Joined Microsoft in 1992; previously EVP of Microsoft's Cloud and Enterprise group, leading the infrastructure shift to Azure."
        },
        {
            "name": "Amy Hood",
            "title": "EVP and CFO",
            "since": "2013",
            "bio": "Oversees global finance and business operations; previously CFO of Microsoft Business Division leading the Skype acquisition."
        },
        {
            "name": "Brad Smith",
            "title": "Vice Chair and President",
            "since": "2015",
            "bio": "Leads global government affairs, compliance, and corporate operations; previously served as General Counsel for 12 years."
        },
        {
            "name": "Judson Althoff",
            "title": "EVP and Chief Commercial Officer",
            "since": "2021",
            "bio": "Drives global commercial sales strategy across enterprise sectors; previously President of Microsoft North America."
        },
        {
            "name": "Rajesh Jha",
            "title": "EVP, Experiences + Devices",
            "since": "2016",
            "bio": "Leads product development for Office 365, Windows, and consumer services; joined Microsoft in 1990 as a software developer."
        },
        {
            "name": "Kathleen Hogan",
            "title": "EVP and Chief Human Resources Officer",
            "since": "2014",
            "bio": "Responsible for culture, talent, and people programs; previously Corporate VP of Microsoft Services and McKinsey consultant."
        }
    ],
    "adobe": [
        {
            "name": "Shantanu Narayen",
            "title": "Chair and CEO",
            "since": "2007",
            "bio": "Joined Adobe in 1998; transformed Adobe by pioneering the creative suite cloud subscription model and driving global expansion."
        },
        {
            "name": "Dan Durn",
            "title": "EVP and CFO",
            "since": "2021",
            "bio": "Directs global financial strategy and operations; previously served as CFO at Applied Materials, NXP, and Freescale."
        },
        {
            "name": "David Wadhwani",
            "title": "President, Digital Media Business",
            "since": "2021",
            "bio": "Responsible for Creative Cloud and Document Cloud products; previously CEO of AppDynamics and Venture Partner at Greylock."
        },
        {
            "name": "Anil Chakravarthy",
            "title": "President, Digital Experience Business",
            "since": "2020",
            "bio": "Drives global Experience Cloud product strategy; previously spent over 5 years as Chief Executive Officer of Informatica."
        },
        {
            "name": "Gloria Chen",
            "title": "EVP and Chief People Officer",
            "since": "2020",
            "bio": "Leads global human resource planning and employee culture; 25-year veteran at Adobe, previously VP of Corporate Strategy."
        },
        {
            "name": "Dana Rao",
            "title": "EVP, General Counsel & Chief Trust Officer",
            "since": "2018",
            "bio": "Directs legal, security operations, and privacy compliance; previously spent 11 years at Microsoft in intellectual property roles."
        }
    ],
    "salesforce": [
        {
            "name": "Marc Benioff",
            "title": "Chair and CEO",
            "since": "1999",
            "bio": "Co-founded Salesforce and pioneered commercial cloud software; previously youngest Vice President in Oracle's history."
        },
        {
            "name": "Amy Weaver",
            "title": "President and CFO",
            "since": "2021",
            "bio": "Directs global financial strategy; joined Salesforce in 2013 and previously served as President and Chief Legal Officer."
        },
        {
            "name": "Brian Millham",
            "title": "President and Chief Operating Officer",
            "since": "2022",
            "bio": "Early employee who joined Salesforce in 1999; leads global sales, customer success, and operations after building commercial teams."
        },
        {
            "name": "Ariel Kelman",
            "title": "President and Chief Marketing Officer",
            "since": "2023",
            "bio": "Oversees global corporate branding; previously served as CMO at Amazon Web Services, Oracle, and security firm FireEye."
        },
        {
            "name": "Sabastian Niles",
            "title": "President and Chief Legal Officer",
            "since": "2023",
            "bio": "Leads global legal affairs and governance; previously senior Partner at Wachtell Lipton specializing in shareholder activism."
        },
        {
            "name": "Nathalie Scardino",
            "title": "EVP and Chief People Officer",
            "since": "2024",
            "bio": "Directs human resources and global recruiting; joined Salesforce in 2014 from corporate recruiting management at Reed Elsevier."
        }
    ],
    "cisco": [
        {
            "name": "Chuck Robbins",
            "title": "Chair and CEO",
            "since": "2015",
            "bio": "Joined Cisco 1997; previously SVP Worldwide Field Operations, UNC Chapel Hill."
        },
        {
            "name": "Mark Patterson",
            "title": "EVP and CFO",
            "since": "2025",
            "bio": "Previously EVP and Chief Strategy Officer at Cisco."
        },
        {
            "name": "Jeetu Patel",
            "title": "President and CPO",
            "since": "2025",
            "bio": "Previously CPO and CSO at Box; joined Cisco in 2020."
        },
        {
            "name": "Francine Katsoudas",
            "title": "EVP and Chief People, Policy & Purpose Officer",
            "since": "2021",
            "bio": "30-year Cisco veteran; Chief People Officer since 2014, UC Berkeley graduate."
        },
        {
            "name": "Dev Stahlkopf",
            "title": "EVP and Chief Legal Officer",
            "since": "2021",
            "bio": "Previously Corporate VP and General Counsel at Microsoft."
        },
        {
            "name": "Liz Centoni",
            "title": "EVP and Chief Customer Experience Officer",
            "since": "2024",
            "bio": "Previously Executive Vice President of Applications and Chief Strategy Officer; 24-year Cisco veteran."
        },
        {
            "name": "Oliver Tuszik",
            "title": "EVP, Global Sales and Chief Sales Officer",
            "since": "2023",
            "bio": "Previously CEO of Computacenter Germany; Director of Global Partner Sales at Cisco."
        },
        {
            "name": "Carrie Palin",
            "title": "SVP and CMO",
            "since": "2022",
            "bio": "Previously CMO at Intel and SVP at Dell Technologies."
        }
    ],
    "cognizant": [
        {
            "name": "Ravi Kumar S",
            "title": "CEO",
            "since": "2023",
            "bio": "Directs global strategic growth and consulting delivery; previously President of Infosys for over 6 years."
        },
        {
            "name": "Jatin Dalal",
            "title": "CFO",
            "since": "2023",
            "bio": "Directs financial planning and corporate investment; previously spent 21 years at Wipro, serving as CFO for over 8 years."
        },
        {
            "name": "Prasad Sankaran",
            "title": "EVP, Software and Platform Engineering",
            "since": "2022",
            "bio": "Directs digital platform engineering frameworks; previously Senior Managing Director at Accenture cloud services."
        },
        {
            "name": "Surya Gummadi",
            "title": "EVP and President, Cognizant Americas",
            "since": "2022",
            "bio": "Directs enterprise sales across North America; 20-year Cognizant veteran, previously heading Healthcare and Life Sciences."
        },
        {
            "name": "Rebecca Schmitt",
            "title": "EVP and Chief People Officer",
            "since": "2020",
            "bio": "Responsible for talent culture; previously VP of HR at Lumileds and held senior human resource roles at PepsiCo."
        },
        {
            "name": "John Kim",
            "title": "EVP, General Counsel & Chief Corporate Affairs Officer",
            "since": "2020",
            "bio": "Directs legal and compliance pipelines; previously served as General Counsel for Subway sandwich restaurants."
        }
    ],
    "juniper": [
        {
            "name": "Rami Rahim",
            "title": "CEO",
            "since": "2014",
            "bio": "Joined Juniper in 1997 as employee number 32; co-founded the engineering team that designed Juniper's flagship M40 router."
        },
        {
            "name": "Ken Miller",
            "title": "EVP and CFO",
            "since": "2016",
            "bio": "Oversees global finance, accounting, and tax; joined Juniper in 2002 and held senior financial operations roles."
        },
        {
            "name": "Aeone Singson",
            "title": "EVP and Chief People Officer",
            "since": "2023",
            "bio": "Directs global talent strategy and culture programs; over 18 years of experience leading tech recruitment portals."
        },
        {
            "name": "Robert Mobassaly",
            "title": "EVP and General Counsel",
            "since": "2021",
            "bio": "Directs legal and intellectual property strategy; joined Juniper in 2012, previously Associate at legal firms."
        },
        {
            "name": "Derrell James",
            "title": "EVP, Customer Experience",
            "since": "2018",
            "bio": "Leads support services and customer engagement; previously head of global services at RingCentral and Xerox."
        },
        {
            "name": "Sujai Hajela",
            "title": "EVP, Mist AI & Cloud",
            "since": "2019",
            "bio": "Co-founded and served as CEO of Mist Systems; previously senior VP of product management at Cisco enterprise routing."
        }
    ],
    "wipro": [
        {
            "name": "Srinivas Pallia",
            "title": "CEO and Managing Director",
            "since": "2024",
            "bio": "32-year Wipro veteran; leads global engineering consulting and digital services, previously CEO of Wipro Americas 1."
        },
        {
            "name": "Aparna C. Iyer",
            "title": "CFO",
            "since": "2023",
            "bio": "Directs global financial operations and planning; joined Wipro in 2003, holding various corporate finance leadership roles."
        },
        {
            "name": "Sanjeev Jain",
            "title": "Chief Operating Officer",
            "since": "2024",
            "bio": "Directs delivery excellence and supply chains; joined Wipro in 2023, previously managing global delivery at Cognizant."
        },
        {
            "name": "Suzanne Dann",
            "title": "CEO, Wipro Americas 2 Strategic Market Unit",
            "since": "2022",
            "bio": "Directs market operations in finance, technology, and manufacturing; previously corporate Vice President at IBM."
        },
        {
            "name": "Biren Anshu",
            "title": "Chief Information Officer",
            "since": "2023",
            "bio": "Responsible for core enterprise applications and security; previously VP of IT at McKinsey & Company."
        },
        {
            "name": "Anupama Trehan",
            "title": "Chief People Officer",
            "since": "2023",
            "bio": "Responsible for corporate talent and culture; previously HR Director at PepsiCo and held roles at various IT firms."
        }
    ]
}

def migrate():
    mock_dir = BASE_DIR / "mock_data"
    for vendor in VENDORS:
        vendor_dir = mock_dir / vendor
        json_file = vendor_dir / "highlights_leadership.json"
        
        data = MOCK_DATA.get(vendor)
        if data:
            payload = {
                "content": json.dumps(data),
                "sources": []
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"Successfully migrated highlights_leadership.json for {vendor.upper()}")

if __name__ == "__main__":
    migrate()
    print("Migration complete!")
