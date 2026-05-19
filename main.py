import uvicorn


def main():
    uvicorn.run(app='app.app:app', port=5000, reload=True)


if __name__ == "__main__":
    main()
