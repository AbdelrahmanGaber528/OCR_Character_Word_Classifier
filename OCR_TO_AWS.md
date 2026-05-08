# Deploying OCR Project to AWS

Deploying your OCR project (Gateway, Word, and Character prediction services) to AWS involves a transition from local Docker containers to a managed, scalable architecture using **Amazon ECS (Elastic Container Service)** and **Fargate**.

Since your services communicate directly via URLs, you will use **AWS Cloud Map** for internal service discovery and an **Application Load Balancer (ALB)** to expose only the Gateway.

---

### Step 1: Push Docker Images to Amazon ECR
You must store your images in **Amazon ECR (Elastic Container Registry)** so ECS can pull them.

1.  **Create Repositories:** Create three private repositories in the ECR console: `ocr-gateway`, `ocr-word`, and `ocr-char`.
2.  **Authenticate Docker:** Use the AWS CLI to log in to your registry:
    ```bash
    aws ecr get-login-password --region <your-region> | docker login --username AWS --password-stdin <aws_account_id>.dkr.ecr.<region>.amazonaws.com
    ```
3.  **Build and Tag:** Build each image locally and tag it with the ECR URI:
    ```bash
    docker build -t ocr-gateway .
    docker tag ocr-gateway:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/ocr-gateway:latest
    ```
4.  **Push:** Upload the images:
    ```bash
    docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/ocr-gateway:latest
    ```

---

### Step 2: Set Up Networking (VPC & Cloud Map)
*   **VPC:** Ensure you have a VPC with at least two Public subnets (for the ALB) and two Private subnets (for your services).
*   **Service Discovery (Cloud Map):** Create a Private DNS Namespace (e.g., `ocr.local`). This allows your Gateway to reach other services using simple hostnames like `http://word.ocr.local`.

---

### Step 3: Create ECS Task Definitions
A "Task Definition" is the blueprint for your container. You need one for each service.

*   **Launch Type:** Select **AWS Fargate**.
*   **Resources:** Allocate CPU and Memory (e.g., 0.5 vCPU and 1GB RAM; OCR models may need more).
*   **Environment Variables:** Add the internal URLs for the Word and Char services to the Gateway's definition (e.g., `WORD_SERVICE_URL=http://word.ocr.local`).
*   **Port Mapping:** Map the container port (usually 80 or 8000 for FastAPI).

---

### Step 4: Deploy with Application Load Balancer
1.  **Create ALB:** In the EC2 console, create an Internet-facing ALB. Select your VPC and Public subnets.
2.  **Target Groups:** Create a target group for the Gateway service only. Use **IP** as the target type (required for Fargate).
3.  **Create ECS Cluster:** In the ECS console, create a new cluster using the Fargate template.
4.  **Create Services:**
    *   **Word & Char Services:** Deploy these first. Under "Networking," enable Service Discovery and join the `ocr.local` namespace. Keep these in Private subnets.
    *   **Gateway Service:** Deploy this last. In the "Load Balancing" section, select your ALB and the Gateway target group.

---

### Step 5: Final Verification
*   **Health Checks:** Ensure your FastAPI apps have a `/health` endpoint. AWS will monitor this to confirm the services are running.
*   **Access:** Copy the DNS Name of your ALB from the EC2 console. You should be able to reach your OCR project via `http://<ALB-DNS-Name>/predict`.
