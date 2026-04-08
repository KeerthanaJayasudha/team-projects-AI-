import matplotlib.pyplot as plt

def generate_chart(df, intent, x_col, y_col, chart_type):

    fig, ax = plt.subplots()

    if chart_type == "Line Chart":
        ax.plot(df[x_col], df[y_col])

    elif chart_type == "Bar Chart":
        ax.bar(df[x_col], df[y_col])

    elif chart_type == "Area Chart":
        ax.fill_between(df[x_col], df[y_col])

    elif chart_type == "Scatter Plot":
        ax.scatter(df[x_col], df[y_col])

    elif chart_type == "Histogram":
        ax.hist(df[y_col], bins=20)

    elif chart_type == "Box Plot":
        ax.boxplot(df[y_col])

    else:
        ax.bar(df[x_col], df[y_col])  # fallback

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} vs {x_col}")

    return fig  # ✅ THIS IS REQUIRED