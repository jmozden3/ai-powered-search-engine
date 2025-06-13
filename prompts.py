simple_search_prompt = """ You are given a user query. Historically, users had to manually write the specific search query syntax themselves and manaully select the filters they want to apply. Your job is to do this for them based on the query. 

###Distinct Values for Filters###

<DocumentType>


<LegalIssues>



<Programs>



###Output Format Guidance###
ly documenttext is searched, not commentary
}


### Examples ###

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
