import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:5000";

function App() {
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [isRegistering, setIsRegistering] = useState(false);

  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);

  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");

  const [taskTitle, setTaskTitle] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [assignedTo, setAssignedTo] = useState("");

  const [commentText, setCommentText] = useState({});

  useEffect(() => {
    if (user) {
      loadProjects();
      loadUsers();
    }
  }, [user]);

  const loadUsers = async () => {
    const response = await fetch(`${API_URL}/users`);
    const data = await response.json();
    setUsers(data);
  };

  const loadProjects = async () => {
    const response = await fetch(
      `${API_URL}/projects?user_id=${user.id}`
    );

    const data = await response.json();
    setProjects(data);
  };

  const loadTasks = async (projectId) => {
    const response = await fetch(
      `${API_URL}/projects/${projectId}/tasks`
    );

    const data = await response.json();
    setTasks(data);
  };

  const handleAuth = async (event) => {
    event.preventDefault();

    const url = isRegistering
      ? `${API_URL}/register`
      : `${API_URL}/login`;

    const body = isRegistering
      ? {
          username: username.trim(),
          email: email.trim(),
          password
        }
      : {
          username: username.trim(),
          password
        };

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body)
    });

    const data = await response.json();

    if (!response.ok) {
      alert(data.error || "Something went wrong");
      return;
    }

    if (isRegistering) {
      alert("Registration successful. Please login.");

      setIsRegistering(false);
      setEmail("");
      setPassword("");

      return;
    }

    setUser(data.user);
    setUsername("");
    setPassword("");
  };

  const createProject = async () => {
    if (!projectName.trim()) {
      alert("Enter a project name");
      return;
    }

    const response = await fetch(
      `${API_URL}/projects`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          name: projectName,
          description: projectDescription,
          owner_id: user.id
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.error);
      return;
    }

    setProjects((previousProjects) => [
      data,
      ...previousProjects
    ]);

    setProjectName("");
    setProjectDescription("");
  };

  const selectProject = (project) => {
    setSelectedProject(project);
    loadTasks(project.id);
  };

  const createTask = async () => {
    if (!taskTitle.trim()) {
      alert("Enter a task title");
      return;
    }

    const response = await fetch(
      `${API_URL}/projects/${selectedProject.id}/tasks`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          title: taskTitle,
          description: taskDescription,
          assigned_to: assignedTo
            ? Number(assignedTo)
            : null
        })
      }
    );

    const data = await response.json();

    if (!response.ok) {
      alert(data.error);
      return;
    }

    setTasks((previousTasks) => [
      data,
      ...previousTasks
    ]);

    setTaskTitle("");
    setTaskDescription("");
    setAssignedTo("");
  };

  const updateTaskStatus = async (
    taskId,
    newStatus
  ) => {
    const response = await fetch(
      `${API_URL}/tasks/${taskId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          status: newStatus
        })
      }
    );

    const updatedTask = await response.json();

    setTasks((previousTasks) =>
      previousTasks.map((task) =>
        task.id === taskId
          ? updatedTask
          : task
      )
    );
  };

  const deleteTask = async (taskId) => {
    const shouldDelete = window.confirm(
      "Delete this task?"
    );

    if (!shouldDelete) {
      return;
    }

    await fetch(
      `${API_URL}/tasks/${taskId}`,
      {
        method: "DELETE"
      }
    );

    setTasks((previousTasks) =>
      previousTasks.filter(
        (task) => task.id !== taskId
      )
    );
  };

  const addComment = async (taskId) => {
    const text = commentText[taskId];

    if (!text || !text.trim()) {
      return;
    }

    const response = await fetch(
      `${API_URL}/tasks/${taskId}/comments`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text,
          user_id: user.id
        })
      }
    );

    if (!response.ok) {
      return;
    }

    const updatedTasks = await fetch(
      `${API_URL}/projects/${selectedProject.id}/tasks`
    );

    const data = await updatedTasks.json();

    setTasks(data);

    setCommentText((previousComments) => ({
      ...previousComments,
      [taskId]: ""
    }));
  };

  if (!user) {
    return (
      <div className="auth-page">

        <div className="auth-card">

          <h1>TaskFlow</h1>

          <p>
            Plan projects. Manage tasks. Work together.
          </p>

          <form onSubmit={handleAuth}>

            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
            />

            {isRegistering && (
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
              />
            )}

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
            />

            <button type="submit">
              {isRegistering
                ? "Create Account"
                : "Login"}
            </button>

          </form>

          <button
            className="switch-button"
            onClick={() =>
              setIsRegistering(!isRegistering)
            }
          >
            {isRegistering
              ? "Already have an account? Login"
              : "Create a new account"}
          </button>

        </div>

      </div>
    );
  }

  return (
    <div className="app">

      <header className="navbar">

        <div>
          <h1>TaskFlow</h1>
          <span>
            Welcome, @{user.username}
          </span>
        </div>

        <button
          onClick={() => {
            setUser(null);
            setSelectedProject(null);
            setTasks([]);
          }}
        >
          Logout
        </button>

      </header>

      <main className="dashboard">

        <aside className="project-sidebar">

          <h2>My Projects</h2>

          <div className="create-project">

            <input
              type="text"
              placeholder="Project name"
              value={projectName}
              onChange={(event) =>
                setProjectName(event.target.value)
              }
            />

            <textarea
              placeholder="Project description"
              value={projectDescription}
              onChange={(event) =>
                setProjectDescription(
                  event.target.value
                )
              }
            />

            <button onClick={createProject}>
              Create Project
            </button>

          </div>

          <div className="project-list">

            {projects.map((project) => (

              <button
                key={project.id}
                className={
                  selectedProject?.id === project.id
                    ? "project-item active"
                    : "project-item"
                }
                onClick={() =>
                  selectProject(project)
                }
              >
                <strong>
                  {project.name}
                </strong>

                <small>
                  {project.description}
                </small>

              </button>

            ))}

          </div>

        </aside>

        <section className="workspace">

          {!selectedProject ? (

            <div className="empty-state">

              <h2>
                Select a project
              </h2>

              <p>
                Choose a project from the sidebar
                to manage its tasks.
              </p>

            </div>

          ) : (

            <>

              <div className="workspace-header">

                <div>
                  <h2>
                    {selectedProject.name}
                  </h2>

                  <p>
                    {selectedProject.description}
                  </p>
                </div>

              </div>

              <div className="task-create">

                <input
                  type="text"
                  placeholder="Task title"
                  value={taskTitle}
                  onChange={(event) =>
                    setTaskTitle(event.target.value)
                  }
                />

                <textarea
                  placeholder="Task description"
                  value={taskDescription}
                  onChange={(event) =>
                    setTaskDescription(
                      event.target.value
                    )
                  }
                />

                <select
                  value={assignedTo}
                  onChange={(event) =>
                    setAssignedTo(event.target.value)
                  }
                >

                  <option value="">
                    Assign to user
                  </option>

                  {users.map((person) => (

                    <option
                      key={person.id}
                      value={person.id}
                    >
                      {person.username}
                    </option>

                  ))}

                </select>

                <button onClick={createTask}>
                  Add Task
                </button>

              </div>

              <div className="board">

                {[
                  "To Do",
                  "In Progress",
                  "Completed"
                ].map((status) => (

                  <div
                    className="column"
                    key={status}
                  >

                    <h3>
                      {status}
                    </h3>

                    {tasks
                      .filter(
                        (task) =>
                          task.status === status
                      )
                      .map((task) => (

                        <div
                          className="task-card"
                          key={task.id}
                        >

                          <h4>
                            {task.title}
                          </h4>

                          <p>
                            {task.description}
                          </p>

                          {task.assigned_user && (

                            <small>
                              Assigned to:{" "}
                              <b>
                                {
                                  task.assigned_user
                                    .username
                                }
                              </b>
                            </small>

                          )}

                          <select
                            value={task.status}
                            onChange={(event) =>
                              updateTaskStatus(
                                task.id,
                                event.target.value
                              )
                            }
                          >

                            <option>
                              To Do
                            </option>

                            <option>
                              In Progress
                            </option>

                            <option>
                              Completed
                            </option>

                          </select>

                          <button
                            className="delete-button"
                            onClick={() =>
                              deleteTask(task.id)
                            }
                          >
                            Delete
                          </button>

                          <div className="comments">

                            {task.comments.map(
                              (comment) => (

                                <p
                                  key={comment.id}
                                >
                                  <b>
                                    @{comment.username}
                                  </b>{" "}
                                  {comment.text}
                                </p>

                              )
                            )}

                          </div>

                          <div className="comment-box">

                            <input
                              type="text"
                              placeholder="Add a comment..."
                              value={
                                commentText[
                                  task.id
                                ] || ""
                              }
                              onChange={(event) =>
                                setCommentText(
                                  (
                                    previousComments
                                  ) => ({
                                    ...previousComments,
                                    [task.id]:
                                      event.target
                                        .value
                                  })
                                )
                              }
                            />

                            <button
                              onClick={() =>
                                addComment(task.id)
                              }
                            >
                              Comment
                            </button>

                          </div>

                        </div>

                      ))}

                  </div>

                ))}

              </div>

            </>

          )}

        </section>

      </main>

    </div>
  );
}

export default App;