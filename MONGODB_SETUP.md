# MongoDB Atlas Setup Guide

## Step 1: Create MongoDB Atlas Account

1. **Go to MongoDB Atlas**: https://www.mongodb.com/cloud/atlas/register
2. **Sign up** with your email or Google account (free tier available)
3. **Verify your email** if required

## Step 2: Create a Cluster

1. **Click "Build a Database"**
2. **Choose "M0 Sandbox" (Free tier)** - This gives you 512MB storage
3. **Select Cloud Provider**: Choose AWS (recommended)
4. **Choose Region**: Select the region closest to your location
5. **Cluster Name**: Enter "creepypasta-cluster" (or any name you prefer)
6. **Click "Create Cluster"**
7. **Wait 3-5 minutes** for cluster creation

## Step 3: Create Database User

1. **Click "Database Access"** in the left sidebar
2. **Click "Add New Database User"**
3. **Choose "Password" authentication**
4. **Username**: Enter username
5. **Password**: Click "Autogenerate Secure Password" and **SAVE THE PASSWORD** (you'll need it!)
6. **Database User Privileges**: Select "Read and write to any database"
7. **Click "Add User"**

## Step 4: Configure Network Access

1. **Click "Network Access"** in the left sidebar
2. **Click "Add IP Address"**
3. **Click "Allow Access from Anywhere"** (0.0.0.0/0) - This allows access from any IP
4. **Click "Confirm"**

## Step 5: Get Connection String

1. **Click "Database"** in the left sidebar
2. **Click "Connect"** on your cluster
3. **Choose "Connect your application"**
4. **Driver**: Select "Python"
5. **Version**: Select "3.6 or later"
6. **Copy the connection string**

## Step 6: Update Your .env File

1. **Open the `.env` file** in your project root
2. **Replace the placeholder** with your actual connection string:
   ```
   MONGODB_URI=
   ```
3. **Save the file**

   **Example format only - use your actual credentials:**
   ```
   MONGODB_URI=
   ```

## Step 7: Test the Connection

Run the migration script to test your connection:

## Step 8: Verify Data in MongoDB Atlas

1. **Go back to MongoDB Atlas**
2. **Click "Browse Collections"** in your cluster
3. **You should see**:
   - Database: `mime`
   - Collection: `creepypasta_stories`
   - Documents with your scraped stories

## Troubleshooting

### Connection Issues
- **Check your password**: Make sure you copied it correctly
- **Check network access**: Ensure "Allow Access from Anywhere" is enabled
- **Check connection string**: Make sure there are no extra spaces or characters

### Migration Issues
- **Check .env file**: Make sure MONGODB_URI is properly set
- **Check internet connection**: MongoDB Atlas requires internet access
- **Check cluster status**: Make sure your cluster is running (not paused)

### Common Errors
- **Authentication failed**: Wrong username/password
- **Network timeout**: Check network access settings
- **SSL errors**: Make sure you're using the `mongodb+srv://` connection string

## Next Steps

Once your MongoDB Atlas is set up and the migration is complete:

1. **Start the Flask app**: `python app.py`
2. **Open your browser**: Go to `http://localhost:5000`
3. **Test the new features**: Browse stories, check genre classification, view statistics
4. **Export training data**: Use the new API endpoints for AI model training

## Free Tier Limits

- **Storage**: 512MB (enough for thousands of stories)
- **Connections**: 100 concurrent connections
- **Data Transfer**: 1GB per month
- **Backup**: 1 backup per cluster

For production use with more data, consider upgrading to a paid plan.
