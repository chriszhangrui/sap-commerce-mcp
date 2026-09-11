// Verified Script: executed_groovy
// Category: general_groovy | Client: Generic
// Date: 2026-09-11 21:19:04
// Tags: 

def typeService = spring.getBean("typeService")
println "ProductReference model class: " + typeService.getModelClass(typeService.getComposedTypeForCode("ProductReference"))
println "ProductReferenceTypeEnum class: " + typeService.getEnumerationType("ProductReferenceTypeEnum")
