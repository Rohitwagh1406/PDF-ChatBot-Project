import os
from flask import Flask, request, render_template, flash, session
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import InputRequired
from werkzeug.utils import secure_filename
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain.document_loaders import PyPDFLoader
from langchain.indexes.vectorstore import VectorstoreIndexCreator
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from io import BytesIO

app = Flask(__name__)

# Set up the secret key for session management
app.secret_key = 'chatbot_secret_key'

# Set up the upload folder and create it if it doesn't exist
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Set OpenAI API key explicitly
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class UploadForm(FlaskForm):
    file = FileField('PDF File', validators=[InputRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=["GET", "POST"])
def home():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash('File uploaded successfully!')
        session["filename"] = filename
    return render_template('index.html', form=form, filename=session.get("filename", None))

@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    filename = session.get("filename", None)

    if not filename:
        return "No file uploaded!", 400

    # Load the PDF document
    loader = PyPDFLoader(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Create OpenAI embeddings
    embeddings = OpenAIEmbeddings()

    # Initialize the VectorstoreIndexCreator with embeddings
    index_creator = VectorstoreIndexCreator(embedding=embeddings)

    # Generate the vectorstore and create the index
    docsearch = index_creator.from_loaders([loader])

    # Perform similarity search on the documents
    docs = docsearch.vectorstore.similarity_search(userText)

    # Construct the prompt for question answering
    prompt = f"""
        Answer the question that is given under triple round brackets with maximum detail.
        Make the answer maximum detailed with respect to your capability.
        Follow the format of the answer that is given in the question, if no information is provided, you can use the format you think is best equipped according to question.
        ((({userText})))
        """

    # Initialize the QA chain and run it
    chain = load_qa_chain(OpenAI(temperature=0), chain_type="stuff")
    answer = chain.run(input_documents=docs, question=prompt)

    return str(answer)

if __name__ == "__main__":
    app.run()