# Yemen Opportunity Navigator

## Domain Definition

### Project Overview

Yemen Opportunity Navigator is a bilingual Retrieval-Augmented Generation (RAG) system designed to help Yemeni youth discover reliable educational, professional, entrepreneurial, and innovation opportunities.

The system will allow users to search and ask questions about scholarships, fellowships, internships, training programs, grants, competitions, startup accelerators, and selected remote opportunities.

Unlike a general-purpose chatbot, the system retrieves information from a curated collection of trusted first-party sources and generates answers grounded in those sources.

## Problem Statement

Young people in Yemen often face difficulty discovering suitable international opportunities because information is distributed across many websites, universities, international organizations, and application portals.

Applicants may need to manually investigate multiple websites to determine:

- whether applicants from Yemen are eligible;
- application deadlines;
- funding availability;
- academic requirements;
- age requirements;
- required documents;
- whether the opportunity is online or in person;
- and whether the opportunity matches their background.

This creates an information-access problem.

## Proposed Solution

The project will create a centralized RAG-based assistant using a curated knowledge base of official opportunity sources.

Users will be able to ask questions such as:

- Which fully funded scholarships accept applicants from Yemen?
- What AI training opportunities are available?
- Which programs are suitable for computer science graduates?
- What documents are required for a specific fellowship?
- Which opportunities are currently open?

The system will retrieve relevant evidence before generating an answer and will provide source attribution.

## Target Users

The primary target users are Yemeni youth, including:

- university students;
- recent graduates;
- young professionals;
- researchers;
- startup founders;
- technology students;
- applicants seeking international opportunities.

## Knowledge Categories

The initial knowledge base includes:

1. Scholarships
2. Fellowships
3. Internships
4. Training programs
5. Innovation competitions
6. Startup accelerators
7. Grants
8. Remote and technology opportunities

## Data Sources

The initial corpus consists of 50 curated first-party official sources.

Sources are selected primarily from:

- governments;
- universities;
- United Nations organizations;
- international development institutions;
- official scholarship programs;
- technology organizations;
- official innovation and startup programs.

Each source will include metadata such as:

- source ID;
- title;
- provider;
- category;
- official URL;
- eligibility;
- funding information;
- deadline;
- opportunity status;
- language;
- date last verified.

## Languages

The system will support Arabic and English queries.

The knowledge base contains primarily English documents, with support for Arabic and multilingual retrieval.

## Expected RAG Architecture

Official Sources
→ Ingestion
→ Text Cleaning
→ Chunking
→ Embeddings
→ Vector Database
→ Hybrid Retrieval
→ Reranking
→ LLM
→ Grounded Answer + Citations

## Evaluation

Retrieval will be evaluated using a set of manually prepared golden questions and Recall@5.

Generation quality will later be evaluated using RAGAS metrics such as faithfulness and answer relevancy.

## Project Goal

The goal is to develop a production-oriented RAG system rather than a simple PDF chatbot.

The final system should demonstrate:

- high-quality source curation;
- document ingestion;
- multilingual processing;
- semantic and hybrid retrieval;
- reranking;
- source citations;
- evaluation;
- automatic source updating;
- deployment;
- and cost analysis.
