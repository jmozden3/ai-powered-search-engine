query_prompt = """ You are given a user query. Historically, users had to manually write the specific search query syntax themselves and manaully select the filters they want to apply. Your job is to do this for them based on the query. 

###Relevant schemas, fields, syntax guidance###

Here are the list of document types you can filter for:

Currently on OFAC's Website
Currently on OFAC's Website
Removed from OFAC's Website
Removed from OFAC's Website
Active
Active
Blocked Property-Related Licenses (Non-Real Estate)
Code of Federal Regulations
Current
Enforcement
Enforcement Releases
General Commercial
Interpretive Rulings
Notable U.S. Federal Court Opnions
OFAC FAQs
OverRuled Research Notes (System Notes)
Primary Sanctions Enforcement
Secondary Sanctions
Specific Licenses
Unpublished Correspondence/Guidance Letters
Advisories
Compliance
Expired/Revoked
General Licenses
Licenses Unrelated to Blocked Property
Non-profit/Humanitarian
OFAC Settlement Agreements
OFAC/USG Statements In Litigation
Other Guidance
Published (incl. Archived/Removed) OFAC-Related Guidance
Revoked
SEC Correspondence on Sanctions
Secondary Sanction Waivers
Secondary Sanctions Enforcement
Select Derivative Designation & Other Targeting Criteria
Terminated from Jan. 2020 Onward
Alerts
Blocked U.S. Real Estate-Related Licenses
Directives & Determinations
Licensing
Miscellaneous
Notable Federal Register Notice Preambles
OFAC Enforcement Correspondence
Parallel BIS Settlement Agreements
U.S. Government Business
Unpublished OFAC-Related Guidance
Criminal Sanctions Enforcement
Information for Industry Groups
Legal Services
Notable Customs Rulings
Statements of Licensing Policy
U.S. Legal Authorities
Excecutive Orders
Notable BIS-Issued Guidance
Repealed/Superseded Regulatory Provisions
Notable Reports to Congress
Other
Statutes
State Department Sanctions Guidance
Current OFAC FAQs
Internal/Intra-Governmental Correspondence
FAQs Removed From OFAC's Website
Notable Blocking/Unblocking Notices
FAQs "Archived" on OFAC's Website
Items Substantively Duplicative of Others in the Research Center
Miscellaneous
Miscellaneous
Other
Miscellaneous



Here is the search syntax: 





###Output Format Guidance###

Structure your output in the following format:

{
    DateIssuedBegin: date?,
    DateIssuedEnd: date?,
    LegalIssue: [string, string...],
    Program: [string, string...],
    DocumentType: [string, string...],
    RegulatoryProvision: [string, string...],
    Published: boolean,
    EnforcementCharacterization: [string, string...],
    NumberOfViolationsLow: int?,
    NumberOfViolationsHigh: int?,
    OFACPenalty: [string, string...],
    AggregatePenalty: [string, string...],
    Industry: [string, string...],
    VoluntaryDisclosure: [{1}, {0}, {-1}], //1=yes, 2=no, -1=Not Stated}
    EgregiousCase: [{1}, {0}, {-1}], //1=yes, 2=no, -1=Not Stated},
    KeyWords: string,
    ExcludeCommentaries: boolean //when true only documenttext is searched, not commentary
}


### Examples ###

User: give me all documents that contain the words "global distribution system"
Assistant: {
<add search query and filters here>
}






"""



question_classification_prompt = """

You are given a user question. Your job is to classify the question into one of the following categories:

1. Basic keyword search and/or filters
2. Advanced document search
3. Aggregation query

### Guidance ###


### Examples ###



"""
