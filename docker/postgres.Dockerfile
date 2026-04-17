FROM postgres:15-alpine

ENV POSTGRES_DB=snrms \
    POSTGRES_USER=snrms \
    POSTGRES_PASSWORD=snrms

EXPOSE 5432
