import './App.css'
import {useState} from 'react'

function App() {
  const [jobDescription, setJobDescription] = useState('')
  const [resume, setResume] = useState(null)
  const [includeAI, setIncludeAI] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isLoading,setIsLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    if(isLoading) return
    setError('')
    setResult(null)
    if(!resume){
      setError('Please Select a PDF')
      return
    }
    if(jobDescription.trim() === ""){
      setError('Please Enter Job Description')
      return
    }
    const formData = new FormData()
    formData.append('resume', resume)
    formData.append('job_description', jobDescription)
    formData.append('include_ai', String(includeAI))
    setIsLoading(true)
    try{
      const response = await fetch("http://localhost:8000/analyze", {
        method: 'POST',
        body: formData,
      })
      const data = await response.json()
      if(!response.ok){
        setError(
          typeof data.detail === 'string' ? data.detail : 'Unable to analyze this resume.'
        )
        return
      }
      setResult(data)
    } catch {
      setError('Could not complete the request. Check that the backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main>
      <h1>ResumePicker</h1>
      <p>Upload a text-based PDF resume (up to 5 MiB) and paste a job description to compare supported skills.</p>
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="resume">Resume Pdf</label>
          <input id="resume" type="file" accept=".pdf" onChange={(e)=> setResume(e.target.files[0] ?? null)}/>
          <p>{resume ? resume.name : 'No PDF selected'}</p>
        </div>
        <div className="form-field">
          <label htmlFor="job-description">Job Description</label>
          <textarea id="job-description" name="job-description" value={jobDescription} rows="4" cols="50" onChange={(e)=>setJobDescription(e.target.value)}/>
          <p>Characters: {jobDescription.length}</p>
        </div>
        <div className="form-field">
          <div className="checkbox-row">
            <label htmlFor="include-ai">Include AI Feedback</label>
            <input type="checkbox" id="include-ai" checked={includeAI} onChange={(e)=>setIncludeAI(e.target.checked)}/>
          </div>
          <p>Enabling AI feedback sends your resume text and job description to Google.</p>
        </div>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={isLoading}>{isLoading ? 'Analyzing...' : 'Analyze'}</button>
      </form>
      {result && (
        <section>
          <h2>Skill comparison</h2>
          <p>Matched Skills: {result.skill_match.matched_skills.join(', ') || 'None'}</p>
          <p>Missing Skills: {result.skill_match.missing_skills.join(', ') || 'None'}</p>
          <p>Supported-skill coverage: {result.skill_match.skill_coverage_percent === null ? 'No supported skills detected in the job description' : `${result.skill_match.skill_coverage_percent}%`}</p>
          <p>
            Coverage measures supported skills found in the job description,
            not overall job suitability.
          </p>
          <p>
            Supported skills: Python, Java, JavaScript, FastAPI, React,
            SQL, Docker, Git. Matching uses keywords and does not
            understand context or negation.
          </p>
          <h2>Ai Feedback</h2>
          {result.ai_status === 'not_requested' && (
            <p>AI Feedback was not requested.</p>
          )}
          {result.ai_status === 'unavailable' && (
            <p>AI feedback is unavailable. Your skill comparison is still shown.</p>
          )}
          {result.ai_status === 'available' && (
            <div>
              <p>{result.ai_feedback.summary}</p>
              <h3>Strengths</h3>
              {result.ai_feedback.strengths.length === 0 ? (<p>None listed.</p>) : (
                <ul>
                  {result.ai_feedback.strengths.map((strength, index) => (
                    <li key={index}>{strength}</li>
                  ))}
                </ul>
              )}
              <h3>Gaps</h3>
              {result.ai_feedback.gaps.length === 0? (<p>None Listed.</p>) : (
                <ul>
                  {result.ai_feedback.gaps.map((gap, index)=>(
                    <li key={index}>{gap}</li>
                  ))}
                </ul>
              )}
              <h3>Suggestions</h3>
              {result.ai_feedback.suggestions.length === 0 ? (<p>None Listed.</p>) : (
                <ul>{result.ai_feedback.suggestions.map((suggestion, index)=>(
                  <li key={index}>{suggestion}</li>
                ))}
                </ul>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  )
}

export default App
