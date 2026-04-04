import { useState } from "react";
import axios from "axios";

function App() {

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [role, setRole] = useState("Employee");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyzeTicket = async () => {

    setLoading(true);

    const response = await axios.post("http://127.0.0.1:8000/triage", {
      title: title,
      description: description,
      user_role: role
    });

    setResult(response.data);
    setLoading(false);
  };

  return (

    <div className="min-h-screen bg-gray-100 flex items-center justify-center">

      <div className="w-full max-w-4xl bg-white shadow-xl rounded-xl p-8">

        <h1 className="text-3xl font-bold text-gray-800 mb-6">
          AI Ticket Triage System
        </h1>

        {/* FORM */}

        <div className="grid grid-cols-1 gap-4">

          <div>
            <label className="font-medium text-gray-700">Ticket Title</label>
            <input
              type="text"
              className="w-full border rounded-lg p-2 mt-1"
              value={title}
              onChange={(e)=>setTitle(e.target.value)}
            />
          </div>

          <div>
            <label className="font-medium text-gray-700">Description</label>
            <textarea
              className="w-full border rounded-lg p-2 mt-1"
              rows="4"
              value={description}
              onChange={(e)=>setDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="font-medium text-gray-700">User Role</label>

            <select
              className="w-full border rounded-lg p-2 mt-1"
              value={role}
              onChange={(e)=>setRole(e.target.value)}
            >
              <option>Employee</option>
              <option>Manager</option>
              <option>Developer</option>
              <option>IT Admin</option>
              <option>CEO</option>
              <option>CTO</option>
              <option>Director</option>
            </select>

          </div>

          <button
            onClick={analyzeTicket}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg mt-2"
          >
            {loading ? "Analyzing..." : "Analyze Ticket"}
          </button>

        </div>

        {/* RESULT PANEL */}

        {result && (

          <div className="mt-8 bg-gray-50 p-6 rounded-lg border">

            <h2 className="text-xl font-semibold mb-4">
              AI Decision
            </h2>

            <div className="grid grid-cols-2 gap-4">

              <div>
                <span className="font-medium">Category:</span>
                <p>{result.category}</p>
              </div>

              <div>
                <span className="font-medium">Priority:</span>
                <p>{result.priority}</p>
              </div>

              <div>
                <span className="font-medium">Escalation Required:</span>
                <p>{result.escalation_required ? "Yes" : "No"}</p>
              </div>

            </div>

            <div className="mt-4">
              <span className="font-medium">Suggested Resolution:</span>
              <p className="mt-1 text-gray-700">
                {result.suggested_resolution}
              </p>
            </div>

          </div>

        )}

      </div>

    </div>

  );
}

export default App;