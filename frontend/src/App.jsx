import './App.css'
import {useEffect, useState} from 'react'

const apiUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '')

async function waitForServer(signal) {
  const deadline = Date.now() + 90_000
  while (Date.now() < deadline) {
    signal.throwIfAborted()
    try {
      const response = await fetch(`${apiUrl}/health`, {
        signal: AbortSignal.any([signal, AbortSignal.timeout(10_000)]),
        cache: 'no-store',
      })
      if (response.ok && (await response.json()).status === 'ok') return
    } catch {
      signal.throwIfAborted()
    }
    await new Promise((resolve) => setTimeout(resolve, 3000))
  }
  throw new Error('Server did not become ready')
}

function App() {
  const [jobDescription, setJobDescription] = useState('')
  const [resume, setResume] = useState(null)
  const [includeAI, setIncludeAI] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [isLoading,setIsLoading] = useState(false)
  const [serverStatus, setServerStatus] = useState('starting')
  const [connectionAttempt, setConnectionAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    waitForServer(controller.signal)
      .then(() => { if (!controller.signal.aborted) setServerStatus('ready') })
      .catch(() => { if (!controller.signal.aborted) setServerStatus('offline') })
    return () => controller.abort()
  }, [connectionAttempt])

  function retryConnection() {
    setServerStatus('starting')
    setConnectionAttempt((attempt) => attempt + 1)
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if(isLoading || serverStatus !== 'ready') return
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
    if (jobDescription.length > 10_000) {
      setError('Job description must be at most 10,000 characters.')
      return
    }
    const formData = new FormData()
    formData.append('resume', resume)
    formData.append('job_description', jobDescription)
    formData.append('include_ai', String(includeAI))
    setIsLoading(true)
    try{
      // A visitor may leave the page open long enough for Render to sleep again.
      setServerStatus('starting')
      await waitForServer(AbortSignal.timeout(95_000))
      setServerStatus('ready')
      const response = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(60_000),
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
      setError('Could not complete the request. The server may be starting or temporarily unavailable. Reconnect and try again.')
      setServerStatus('offline')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main>
      <h1>ResumePicker</h1>
      <p>Upload a text-based PDF resume (up to 5 MiB, 10 pages, and 30,000 extracted characters) and paste a job description to compare supported skills.</p>
      <p role="status">
        {serverStatus === 'starting' && 'Starting the server—this may take about a minute. You can prepare your PDF and job description while you wait.'}
        {serverStatus === 'ready' && 'Server ready.'}
        {serverStatus === 'offline' && 'The server is taking longer than expected. Please try reconnecting.'}
      </p>
      {serverStatus === 'offline' && <button type="button" onClick={retryConnection} disabled={isLoading}>Reconnect</button>}
      <form onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="resume">Resume Pdf</label>
          <input id="resume" type="file" accept=".pdf" onChange={(e)=> setResume(e.target.files[0] ?? null)}/>
          <p>{resume ? resume.name : 'No PDF selected'}</p>
        </div>
        <div className="form-field">
          <label htmlFor="job-description">Job Description</label>
          <textarea id="job-description" name="job-description" value={jobDescription} rows="4" cols="50" onChange={(e)=>setJobDescription(e.target.value)}/>
          <p>Characters: {jobDescription.length} / 10,000</p>
        </div>
        <div className="form-field">
          <div className="checkbox-row">
            <label htmlFor="include-ai">Include AI Feedback</label>
            <input type="checkbox" id="include-ai" checked={includeAI} onChange={(e)=>setIncludeAI(e.target.checked)}/>
          </div>
          <p>Enabling AI feedback sends your resume text and job description to Google.</p>
          <p>This demo shares a limited AI allowance across visitors. If it is exhausted, your skill comparison will still work.</p>
        </div>
        {error && <p role="alert">{error}</p>}
        <button type="submit" disabled={isLoading || serverStatus !== 'ready'}>{isLoading ? 'Analyzing...' : 'Analyze'}</button>
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
