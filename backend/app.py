from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# -------------------------
# Database Models
# -------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    status = db.Column(
        db.String(30),
        default="To Do"
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey("project.id"),
        nullable=False
    )

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    text = db.Column(
        db.Text,
        nullable=False
    )

    task_id = db.Column(
        db.Integer,
        db.ForeignKey("task.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


# -------------------------
# Helper Functions
# -------------------------

def user_data(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }


def project_data(project):
    member_count = ProjectMember.query.filter_by(
        project_id=project.id
    ).count()

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "owner_id": project.owner_id,
        "member_count": member_count,
        "created_at": project.created_at.strftime(
            "%Y-%m-%d %H:%M"
        )
    }


def task_data(task):
    assigned_user = None

    if task.assigned_to:
        user = db.session.get(
            User,
            task.assigned_to
        )

        if user:
            assigned_user = user_data(user)

    comments = TaskComment.query.filter_by(
        task_id=task.id
    ).order_by(
        TaskComment.id.asc()
    ).all()

    comment_list = []

    for comment in comments:
        user = db.session.get(
            User,
            comment.user_id
        )

        comment_list.append({
            "id": comment.id,
            "text": comment.text,
            "username": user.username if user else "Unknown",
            "created_at": comment.created_at.strftime(
                "%Y-%m-%d %H:%M"
            )
        })

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "project_id": task.project_id,
        "assigned_user": assigned_user,
        "comments": comment_list,
        "created_at": task.created_at.strftime(
            "%Y-%m-%d %H:%M"
        )
    }


# -------------------------
# Home
# -------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "TaskFlow API is running"
    })


# -------------------------
# Register
# -------------------------

@app.route(
    "/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({
            "error": "All fields are required"
        }), 400

    existing_user = User.query.filter(
        (User.username == username) |
        (User.email == email)
    ).first()

    if existing_user:
        return jsonify({
            "error": "Username or email already exists"
        }), 409

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password)
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "Registration successful",
        "user": user_data(user)
    }), 201


# -------------------------
# Login
# -------------------------

@app.route(
    "/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(
        username=username
    ).first()

    if not user:
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    if not check_password_hash(
        user.password,
        password
    ):
        return jsonify({
            "error": "Invalid username or password"
        }), 401

    return jsonify({
        "message": "Login successful",
        "user": user_data(user)
    })


# -------------------------
# Get Users
# -------------------------

@app.route(
    "/users",
    methods=["GET"]
)
def get_users():

    users = User.query.order_by(
        User.username.asc()
    ).all()

    return jsonify([
        user_data(user)
        for user in users
    ])


# -------------------------
# Create Project
# -------------------------

@app.route(
    "/projects",
    methods=["POST"]
)
def create_project():

    data = request.get_json()

    name = data.get("name", "").strip()
    description = data.get(
        "description",
        ""
    ).strip()
    owner_id = data.get("owner_id")

    if not name or not owner_id:
        return jsonify({
            "error": "Project name and owner are required"
        }), 400

    owner = db.session.get(
        User,
        owner_id
    )

    if not owner:
        return jsonify({
            "error": "Owner not found"
        }), 404

    project = Project(
        name=name,
        description=description,
        owner_id=owner_id
    )

    db.session.add(project)
    db.session.flush()

    owner_member = ProjectMember(
        project_id=project.id,
        user_id=owner_id
    )

    db.session.add(owner_member)
    db.session.commit()

    return jsonify(
        project_data(project)
    ), 201


# -------------------------
# Get Projects
# -------------------------

@app.route(
    "/projects",
    methods=["GET"]
)
def get_projects():

    user_id = request.args.get(
        "user_id",
        type=int
    )

    if not user_id:
        return jsonify([])

    project_ids = db.session.query(
        ProjectMember.project_id
    ).filter_by(
        user_id=user_id
    ).subquery()

    projects = Project.query.filter(
        Project.id.in_(project_ids)
    ).order_by(
        Project.id.desc()
    ).all()

    return jsonify([
        project_data(project)
        for project in projects
    ])


# -------------------------
# Add User to Project
# -------------------------

@app.route(
    "/projects/<int:project_id>/members",
    methods=["POST"]
)
def add_member(project_id):

    data = request.get_json()

    user_id = data.get("user_id")

    project = db.session.get(
        Project,
        project_id
    )

    user = db.session.get(
        User,
        user_id
    )

    if not project or not user:
        return jsonify({
            "error": "Project or user not found"
        }), 404

    existing_member = ProjectMember.query.filter_by(
        project_id=project_id,
        user_id=user_id
    ).first()

    if existing_member:
        return jsonify({
            "error": "User is already a project member"
        }), 409

    member = ProjectMember(
        project_id=project_id,
        user_id=user_id
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({
        "message": "User added to project"
    }), 201


# -------------------------
# Create Task
# -------------------------

@app.route(
    "/projects/<int:project_id>/tasks",
    methods=["POST"]
)
def create_task(project_id):

    data = request.get_json()

    title = data.get(
        "title",
        ""
    ).strip()

    description = data.get(
        "description",
        ""
    ).strip()

    assigned_to = data.get(
        "assigned_to"
    )

    project = db.session.get(
        Project,
        project_id
    )

    if not project:
        return jsonify({
            "error": "Project not found"
        }), 404

    if not title:
        return jsonify({
            "error": "Task title is required"
        }), 400

    task = Task(
        title=title,
        description=description,
        project_id=project_id,
        assigned_to=assigned_to
    )

    db.session.add(task)
    db.session.commit()

    return jsonify(
        task_data(task)
    ), 201


# -------------------------
# Get Project Tasks
# -------------------------

@app.route(
    "/projects/<int:project_id>/tasks",
    methods=["GET"]
)
def get_tasks(project_id):

    tasks = Task.query.filter_by(
        project_id=project_id
    ).order_by(
        Task.id.desc()
    ).all()

    return jsonify([
        task_data(task)
        for task in tasks
    ])


# -------------------------
# Update Task Status
# -------------------------

@app.route(
    "/tasks/<int:task_id>",
    methods=["PUT"]
)
def update_task(task_id):

    task = db.session.get(
        Task,
        task_id
    )

    if not task:
        return jsonify({
            "error": "Task not found"
        }), 404

    data = request.get_json()

    if "title" in data:
        task.title = data["title"]

    if "description" in data:
        task.description = data["description"]

    if "status" in data:
        allowed_statuses = [
            "To Do",
            "In Progress",
            "Completed"
        ]

        if data["status"] not in allowed_statuses:
            return jsonify({
                "error": "Invalid task status"
            }), 400

        task.status = data["status"]

    if "assigned_to" in data:
        task.assigned_to = data["assigned_to"]

    db.session.commit()

    return jsonify(
        task_data(task)
    )


# -------------------------
# Delete Task
# -------------------------

@app.route(
    "/tasks/<int:task_id>",
    methods=["DELETE"]
)
def delete_task(task_id):

    task = db.session.get(
        Task,
        task_id
    )

    if not task:
        return jsonify({
            "error": "Task not found"
        }), 404

    TaskComment.query.filter_by(
        task_id=task.id
    ).delete()

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "message": "Task deleted successfully"
    })


# -------------------------
# Add Task Comment
# -------------------------

@app.route(
    "/tasks/<int:task_id>/comments",
    methods=["POST"]
)
def add_task_comment(task_id):

    data = request.get_json()

    text = data.get(
        "text",
        ""
    ).strip()

    user_id = data.get(
        "user_id"
    )

    task = db.session.get(
        Task,
        task_id
    )

    if not task:
        return jsonify({
            "error": "Task not found"
        }), 404

    if not text:
        return jsonify({
            "error": "Comment cannot be empty"
        }), 400

    user = db.session.get(
        User,
        user_id
    )

    if not user:
        return jsonify({
            "error": "User not found"
        }), 404

    comment = TaskComment(
        text=text,
        task_id=task_id,
        user_id=user_id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({
        "id": comment.id,
        "text": comment.text,
        "username": user.username,
        "created_at": comment.created_at.strftime(
            "%Y-%m-%d %H:%M"
        )
    }), 201


# -------------------------
# Start Server
# -------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        debug=True
    )