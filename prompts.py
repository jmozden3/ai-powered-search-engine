query_prompt = """ You are given a user query. Historically, users had to manually write the specific search query syntax themselves and manaully select the filters they want to apply. Your job is to do this for them based on the query. 

###Relevant schemas, fields, syntax guidance###

Here are the list of document types you can filter for:




Here is the search syntax: 





###Output Format Guidance###

Structure your output in the following format:




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
